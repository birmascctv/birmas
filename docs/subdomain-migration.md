# Birmas CCTV System — Moving the Dashboard to a Subdomain

Today the dashboard is reached by public IP only:
`https://170.64.149.147/dashboard`, with a **self-signed** TLS cert
(`/etc/nginx/ssl/birmas.crt`) and a CORS allowlist in
`backend/app.py` hardcoded to that IP. Moving to a subdomain (e.g.
`cctv.yourdomain.com`) is mostly a DNS + nginx + certbot change — no
frontend/backend code restructuring needed, since the SPA already talks
to the backend via relative `/api`, `/ws`, `/stream` paths (see
`frontend/src/api.js`, `LivePlayer.vue`) rather than a hardcoded host.

Replace `cctv.yourdomain.com` below with your actual subdomain.

## Step 1 — Point DNS at the server

You need to control DNS for the domain you want the subdomain under
(registrar's DNS panel, or Cloudflare/Route53/etc. if you use one).

1. Log in to wherever that domain's DNS is managed.
2. Add an **A record**:
   - Name/Host: `cctv` (so the full name resolves to `cctv.yourdomain.com`)
   - Type: `A`
   - Value: `170.64.149.147` (the droplet's public IP)
   - TTL: default/low (e.g. 300s) while testing, can raise later
3. Wait for propagation (usually minutes, can take up to ~1 hour). Verify:
   ```bash
   dig +short cctv.yourdomain.com
   # should print 170.64.149.147
   ```
   If it prints nothing or a different IP, DNS hasn't propagated yet —
   wait and retry before continuing.

> If the server is also fronted by Cloudflare (orange-cloud proxy), turn
> the proxy **off** (grey cloud, "DNS only") for this record until after
> certbot successfully issues a certificate — certbot's HTTP-01 challenge
> needs to reach the origin server directly the first time.

## Step 2 — Get a real TLS certificate for the subdomain

The server already has `certbot` installed (used for the other sites on
this box, `journey.bsh.co.id` / `link.kanto.id`). The self-signed cert
currently used for the IP-only site (`/etc/nginx/ssl/birmas.crt`) won't
validate for a real hostname and will show browser warnings — get a free
Let's Encrypt cert instead:

```bash
sudo certbot --nginx -d cctv.yourdomain.com
```
This requires an nginx `server {}` block whose `server_name` already
matches `cctv.yourdomain.com` and is reachable on port 80 (see Step 3 —
do Step 3 first, then run certbot, since certbot edits the block it
finds by `server_name` and auto-adds the 443/ssl_certificate lines).
Certbot will also offer to set up auto-renewal (a systemd timer,
`certbot.timer`, already installed) and can optionally redirect HTTP→HTTPS
for you automatically when asked.

## Step 3 — Add an nginx server block for the subdomain

Create a new server block (or adapt the existing `deploy/nginx-birmas.conf`)
so `server_name` matches the subdomain instead of the bare IP:

```nginx
# /etc/nginx/sites-available/birmas-subdomain
server {
    listen 80;
    server_name cctv.yourdomain.com;

    root  /root/birmas/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/users/login {
        limit_req zone=login burst=3 nodelay;
        proxy_pass         http://127.0.0.1:8000/api/users/login;
        proxy_http_version 1.1;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }

    location /api/ {
        limit_req zone=api burst=30 nodelay;
        proxy_pass         http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass         http://127.0.0.1:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade $http_upgrade;
        proxy_set_header   Connection "upgrade";
        proxy_set_header   Host $host;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }

    location /stream/ {
        proxy_pass         http://127.0.0.1:8888/;
        proxy_http_version 1.1;
        proxy_set_header   Host $host;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/birmas-subdomain /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```
Then run the `certbot --nginx -d cctv.yourdomain.com` command from Step 2
— it will find this block by `server_name`, obtain the cert, and rewrite
this file in place to add the `listen 443 ssl;` + `ssl_certificate` lines
and an HTTP→HTTPS redirect block.

**Decide whether to keep the old IP-based site running side by side.**
You can leave the existing `170.64.149.147` HTTPS block in
`/etc/nginx/sites-enabled/birmas` active (both can coexist — nginx routes
by `server_name`/SNI), or remove it once the subdomain is confirmed
working, so only one canonical URL remains. If you keep both, make sure
`server_name` values don't overlap/conflict between the two files.

## Step 4 — Update backend CORS allowlist

`backend/app.py` currently only allows the bare IP as an origin:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://170.64.149.147",
        "http://170.64.149.147:5173",
        "https://170.64.149.147",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    ...
)
```
Add the new subdomain (and drop the IP-based entries later if you retire
that URL):
```python
    allow_origins=[
        "https://cctv.yourdomain.com",
        "http://170.64.149.147",       # remove once migration is confirmed
        "http://170.64.149.147:5173",
        "https://170.64.149.147",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
```
Restart the backend after editing: `sudo systemctl restart backend` (or
whatever the backend's actual service name is — check
`systemctl list-units | grep birmas` / the developer guide's services
table).

## Step 5 — Verify end-to-end

```bash
curl -I https://cctv.yourdomain.com/dashboard        # expect 200, valid cert (no -k needed)
curl -I https://cctv.yourdomain.com/stream/cam1/main_stream.m3u8
curl -I https://cctv.yourdomain.com/api/products
```
Open the dashboard in a browser at the new URL and confirm: no cert
warning, live feed plays, login works, WebSocket toast notifications
still arrive (browser console should show `wss://cctv.yourdomain.com/ws/events`
connecting, not the old IP).

## Step 6 — Git sync

This migration only touches server-side files (nginx config, `.env`/CORS
in `backend/app.py`). As always: commit the `backend/app.py` CORS change
and the new nginx site config (add it under `deploy/`, mirroring
`deploy/nginx-birmas.conf`) to the repo, push, then `git pull` on the Pi
so its copy matches — even though the Pi doesn't run nginx/backend itself,
keeping the whole repo in sync avoids confusion later.

## Notes / things that do NOT need to change

- **No frontend code changes** — `frontend/src/api.js` uses a relative
  `baseURL: '/api'`, and `LivePlayer.vue` uses relative `/stream/...` —
  both already domain-agnostic.
- **WireGuard tunnel (Pi ↔ server) is unaffected** — it's a private
  `10.0.0.0/24` overlay, entirely separate from the public-facing
  domain/TLS setup.
- **MediaMTX itself doesn't need a hostname** — nginx is the only thing
  that proxies `/stream/` to it, and that's already relative.
