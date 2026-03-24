# Deployment Configuration Notes

These files document system-level configs that live outside the repo.

## System files to apply after fresh deploy:

### nginx
```
cp deploy/nginx-birmas.conf /etc/nginx/sites-available/birmas
ln -sf /etc/nginx/sites-available/birmas /etc/nginx/sites-enabled/birmas
systemctl reload nginx
```

### Backend systemd
```
cp deploy/backend.service /etc/systemd/system/backend.service
systemctl daemon-reload && systemctl restart backend
```

### PostgreSQL - bind to localhost only
Edit `/etc/postgresql/16/main/postgresql.conf`:
```
listen_addresses = 'localhost'
```

### MediaMTX - restrict API to localhost
In `~/mediamtx.yml`:
```
apiAddress: 127.0.0.1:9997
```

### Pi - journald cap
```
/etc/systemd/journald.conf.d/birmas.conf:
[Journal]
SystemMaxUse=50M
MaxRetentionSec=2weeks
```

### Pi - health check cron
```
*/5 * * * * /home/birmas1/birmas/scripts/pi_health_check.sh
```
