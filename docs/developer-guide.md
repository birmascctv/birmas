# Birmas CCTV System — Developer Guide

Practical guide for working on this codebase: repo layout, environments,
how to run/deploy each piece, and common maintenance tasks. Pair this with
`architecture.md` (what the system does) and `network-diagram.md` /
`api-diagram.md` (how the pieces talk to each other).

## Repo layout (`~/birmas`)

```
birmas/
├── backend/            FastAPI app — events, users, stats REST + WebSocket
│   ├── app.py           App entrypoint, CORS, router wiring, /ws/events
│   ├── db.py             SQLAlchemy engine/session (PostgreSQL)
│   ├── models.py         SQLAlchemy models: User, Event, Product
│   ├── schemas.py         Pydantic request/response schemas
│   └── routes/            events.py, users.py, stats.py, stream.py
├── frontend/            Vue 3 + Vite SPA
│   ├── src/pages/         Dashboard.vue, Login.vue
│   ├── src/components/    LivePlayer, EventTable, CountChart, StatsBar,
│   │                      TimelineScrubber, ToastNotif
│   ├── src/api.js          fetch/axios wrapper for backend calls
│   └── dist/               production build served by nginx (git-ignored)
├── inference/            Runs ONLY on the Raspberry Pi
│   ├── main.py             RTSP capture → YOLO → tracker → POST /api/events
│   ├── tracker.py           ProductTracker: local IoU-based tracker
│   └── models/best.pt       Deployed YOLO weights (NOT in git, scp'd manually)
├── systemd/              Service unit files (installed manually on each host)
│   ├── inference.service         (Pi)
│   └── ffmpeg-publisher.service  (Pi)
├── training_results/     Uploaded Kaggle training runs (results.csv, args.yaml,
│                          weights/, confusion matrices) — NOT in git
├── storage/frames/       JPEG frame captures saved per detection event
├── scripts/, tools/       Maintenance/one-off scripts
├── requirements.txt       Full-stack Python deps (backend + a superset of
│                          inference deps — Pi installs a curated subset)
└── docs/                  This directory (architecture, network, API, guide)
```

## Hosts involved

| Host | Role | How to reach |
|---|---|---|
| DigitalOcean droplet | Server: backend, DB, MediaMTX, nginx, frontend build | `ssh root@170.64.149.147` |
| Raspberry Pi 4B | Store edge device: camera relay + inference | `ssh birmas1@10.0.0.2` (over WireGuard, once tunnel is up) |

Both hosts run their own clone of the same git repo at `~/birmas` (root's
home on the server, `birmas1`'s home on the Pi). **Keep them in sync** —
see "Git workflow" below.

## Environment setup

### Server — backend
```bash
cd ~/birmas
python3 -m venv venv          # already exists; recreate only if corrupted
source venv/bin/activate
pip install -r requirements.txt
# .env must define: DATABASE_URL (postgresql+psycopg2://...), SECRET_KEY,
# ALERT_EMAIL_FROM/TO/APP_PASSWORD (optional, for email alerts)
uvicorn backend.app:app --host 0.0.0.0 --port 8000   # for local testing;
# production runs this via a systemd/process manager — check
# `systemctl status backend` on the server for the real launch command.
```

### Server — frontend build
```bash
cd ~/birmas/frontend
npm install
npm run build       # outputs to dist/, served directly by nginx — no dev server in prod
npm run dev          # local dev server (vite), proxies /api and /stream — see vite.config.js
```
After any frontend change destined for production: **always run
`npm run build`** and confirm nginx is serving the new `dist/` (nginx just
serves static files, no restart needed unless the nginx config itself
changed).

### Server — nginx config
- Global config: `/etc/nginx/nginx.conf`, tracked in the repo at
  `deploy/nginx.conf` (added 2026-07-20 — previously untracked). Site
  config: `deploy/nginx-birmas.conf` → `/etc/nginx/sites-enabled/birmas`.
- **`gzip_types` must include `application/json`.** `gzip on;` alone only
  compresses `text/html` by nginx's built-in default — it does **not**
  compress JSON. This was found 2026-07-20 to be a real cause of slow
  dashboard loads: the dashboard's components (`StatsBar`, `CountChart`,
  `EventTable`, `TimelineScrubber`) each independently fetch up to 5000
  raw events on mount, and an uncompressed 5000-row `/api/events` response
  is ~1.1MB vs ~120KB gzip'd. If you ever regenerate `nginx.conf` from a
  fresh install/template, re-apply the uncommented `gzip_types` line (see
  `deploy/nginx.conf`) — don't leave it on the commented-out Debian
  default.
- After any nginx config edit: `sudo nginx -t` (validate) then
  `sudo systemctl reload nginx` (no dropped connections, unlike `restart`).

### Raspberry Pi — inference
```bash
cd ~/birmas
# venv was built with --system-site-packages to reuse apt-installed
# ARM wheels for opencv/torch/scipy/torchvision (pip-compiling these on Pi
# from source is slow and has previously caused OOM crashes):
python3 -m venv --system-site-packages venv
source venv/bin/activate
pip install ultralytics==8.3.199 requests python-dotenv
# Required apt packages (if not already present):
sudo apt install python3-opencv python3-scipy python3-torch \
                  python3-torchvision python3-matplotlib python3-pil
```

## Running the services

### Install/enable a systemd service (either host)
```bash
sudo cp systemd/<name>.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now <name>
sudo systemctl status <name> --no-pager
journalctl -u <name> -f          # tail logs live
```

### Services and where they run
| Service | Host | Purpose |
|---|---|---|
| `inference.service` | Pi | Runs `inference/main.py` continuously |
| `ffmpeg-publisher.service` | Pi | Relays camera RTSP to server MediaMTX |
| `mediamtx.service` | Server | RTSP/HLS media server |
| `backend.service` | Server | uvicorn FastAPI app |
| `nginx.service` | Server | TLS termination, reverse proxy, static SPA |
| `pocketbase.service` | Server | Unrelated landing-page backend (Kanto) — not part of CCTV pipeline |

### Health checks
```bash
# Is the camera feed actually flowing? (run on server)
curl -s http://localhost:9997/v3/paths/list | python3 -m json.tool
# Look for "ready": true on both cam1 and cam1_raw.
# If false but Pi is reachable (ping/ssh OK), restart the publisher on the Pi:
ssh birmas1@10.0.0.2 "sudo systemctl restart ffmpeg-publisher"

# Is inference producing detections? (run on Pi)
journalctl -u inference -f
# Look for "[DEBUG] Frame N: X detections" lines.

# Is the API reachable from the Pi? (run on Pi)
curl -s http://10.0.0.1:8000/api/camera-status
```

## Swapping the YOLO model

Model weights are **never committed to git** (`.gitignore` blocks `*.pt`
globally to keep the repo small). To deploy a newly-trained model:

```bash
# 1. Upload the new training run to the server, e.g. via scp:
scp -r local/path/run_name root@170.64.149.147:/root/birmas/training_results/

# 2. Compare metrics before swapping — don't just take the newest run blindly:
python3 -c "
import csv
rows = list(csv.DictReader(open('training_results/run_name/results.csv')))
best = max(rows, key=lambda r: float(r['metrics/mAP50(B)']))
print(best)
"
# Compare precision/recall/mAP50/mAP50-95 against the currently deployed
# model's own best-epoch stats before replacing.

# 3. If genuinely better, copy the weights into the deployed location:
cp training_results/run_name/weights/best.pt inference/models/best.pt

# 4. Sync to the Pi (inference.service reads ./models/best.pt relative to
#    its working directory — no service restart needed for the copy itself,
#    but restart to force the process to reload the new weights):
scp inference/models/best.pt birmas1@10.0.0.2:~/birmas/inference/models/best.pt
ssh birmas1@10.0.0.2 "sudo systemctl restart inference"
```

## Git workflow (keep server, Pi, and GitHub in sync)

```bash
# On whichever host you made changes:
cd ~/birmas
git add -A
git commit -m "..."
git push origin main

# On the OTHER host(s):
cd ~/birmas
git pull origin main

# Restart any affected services after pulling code changes:
sudo systemctl restart <affected-service>
```
Do this **every time** you change backend/frontend/inference code — the
server and Pi do not auto-sync. Model weights (`*.pt`) and
`training_results/` are handled separately via `scp` (see above), since
they're git-ignored.

## Reconnecting the Pi after a network/IP change

If the Pi's WiFi SSID, camera IP, or WireGuard keys change (e.g. after an
SD card rewrite), the fix sequence has historically been:
1. Regenerate/confirm WireGuard keypair on the Pi (`wg genkey`, `wg pubkey`).
2. Add/update the peer entry in the server's `/etc/wireguard/wg0.conf`
   (`PublicKey`, `AllowedIPs = 10.0.0.2/32`), then
   `sudo wg syncconf wg0 <(wg-quick strip wg0)` or restart `wg-quick@wg0`.
3. Confirm handshake: `sudo wg show` on the server should show a recent
   `latest handshake`.
4. Update `STREAM_URL` in `systemd/ffmpeg-publisher.service` and
   `inference.service` if the camera's LAN IP changed.
5. Re-clone or `git pull` the repo on the Pi if the SD card was wiped.
6. Recreate the Pi's Python venv (see "Environment setup" above).

## Known gotchas

- **`ffmpeg-publisher` can silently stall** (process alive, socket dead, no
  crash/restart) — always check MediaMTX's `paths/list` `ready` flag first
  when live feed goes blank, not just ping/SSH to the Pi.
- **`inference/tracker.py` was previously broken** (imported a nonexistent
  `yolox_tracker` package) — it's now a self-contained IoU tracker with
  zero external dependencies beyond `numpy`. Don't reintroduce an external
  tracker dependency without confirming it's actually installable on the
  Pi's ARM/Python 3.13 environment first.
- **Pi is CPU-only** — any model or pipeline change should be evaluated for
  inference latency on-device, not just accuracy in Kaggle/Colab.
- **`MODEL_PATH=./models/best.pt` is relative** to `inference/`'s working
  directory (`systemd`'s `WorkingDirectory=`) — swapping the file in place
  is sufficient; no service file edits needed for a model-only update.
