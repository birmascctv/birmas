#!/bin/bash
# Birmas Health Check & Alerting
# Runs every 5 minutes via cron, logs to /root/birmas/logs/health.log
#
# HOW TO ENABLE EMAIL ALERTS (Gmail):
#   1. Go to https://myaccount.google.com/security
#   2. Make sure 2-Step Verification is ON (required for App Passwords)
#   3. Go to https://myaccount.google.com/apppasswords
#   4. Create a new App Password (name it "Birmas Server")
#   5. Copy the 16-character password (e.g. abcd efgh ijkl mnop)
#   6. Open /root/birmas/.env and set:
#        ALERT_EMAIL_APP_PASSWORD=abcdefghijklmnop   (no spaces)
#   That's it — email alerts activate automatically.
#
# NOTE: Your regular Gmail password does NOT work here. Gmail requires
#       App Passwords for SMTP. This is a Google security requirement.

# Load credentials from .env (keeps passwords out of this script/git)
ENV_FILE="/root/birmas/.env"
if [ -f "$ENV_FILE" ]; then
    ALERT_EMAIL_FROM=$(grep    '^ALERT_EMAIL_FROM='         "$ENV_FILE" | cut -d= -f2-)
    ALERT_EMAIL_TO=$(grep      '^ALERT_EMAIL_TO='           "$ENV_FILE" | cut -d= -f2-)
    ALERT_EMAIL_APP_PASSWORD=$(grep '^ALERT_EMAIL_APP_PASSWORD=' "$ENV_FILE" | cut -d= -f2-)
fi

LOG="/root/birmas/logs/health.log"
NOW=$(date '+%Y-%m-%d %H:%M:%S')

# Alert cooldown — don't repeat the same alert more than once per 30 minutes
COOLDOWN_FILE="/tmp/birmas_alert_cooldown"
COOLDOWN_SECS=1800

_can_alert() {
    local key="$1"
    local stamp_file="${COOLDOWN_FILE}_${key}"
    local now_epoch; now_epoch=$(date +%s)
    if [ -f "$stamp_file" ]; then
        local last; last=$(cat "$stamp_file")
        if (( now_epoch - last < COOLDOWN_SECS )); then
            return 1  # still cooling down
        fi
    fi
    echo "$now_epoch" > "$stamp_file"
    return 0
}

send_alert() {
    local key="$1"
    local msg="$2"
    echo "[$NOW] ALERT: $msg" >> "$LOG"
    if [ -n "$ALERT_EMAIL_APP_PASSWORD" ] && [ -n "$ALERT_EMAIL_TO" ]; then
        if _can_alert "$key"; then
            python3 -c "
import smtplib, os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
msg = MIMEMultipart()
msg['From']    = '${ALERT_EMAIL_FROM}'
msg['To']      = '${ALERT_EMAIL_TO}'
msg['Subject'] = '[Birmas] Alert: ${key}'
body = '''🚨 BIRMAS ALERT

Issue : ${msg}
Server: 170.64.149.147
Time  : ${NOW}

---
This is an automated alert from your Birmas monitoring system.
Check https://170.64.149.147/dashboard for details.
'''
msg.attach(MIMEText(body, 'plain'))
try:
    s = smtplib.SMTP('smtp.gmail.com', 587, timeout=10)
    s.starttls()
    s.login('${ALERT_EMAIL_FROM}', '${ALERT_EMAIL_APP_PASSWORD}')
    s.sendmail('${ALERT_EMAIL_FROM}', '${ALERT_EMAIL_TO}', msg.as_string())
    s.quit()
    print('email sent')
except Exception as e:
    print(f'email failed: {e}')
" >> "$LOG" 2>&1
        fi
    fi
}

send_recovery() {
    local key="$1"
    local msg="$2"
    local stamp_file="${COOLDOWN_FILE}_${key}"
    echo "[$NOW] RECOVERY: $msg" >> "$LOG"
    rm -f "$stamp_file"  # reset cooldown so next failure alerts immediately
    if [ -n "$ALERT_EMAIL_APP_PASSWORD" ] && [ -n "$ALERT_EMAIL_TO" ]; then
        python3 -c "
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
msg = MIMEMultipart()
msg['From']    = '${ALERT_EMAIL_FROM}'
msg['To']      = '${ALERT_EMAIL_TO}'
msg['Subject'] = '[Birmas] Recovered: ${key}'
body = '''✅ BIRMAS RECOVERED

Status: ${msg}
Server: 170.64.149.147
Time  : ${NOW}
'''
msg.attach(MIMEText(body, 'plain'))
try:
    s = smtplib.SMTP('smtp.gmail.com', 587, timeout=10)
    s.starttls()
    s.login('${ALERT_EMAIL_FROM}', '${ALERT_EMAIL_APP_PASSWORD}')
    s.sendmail('${ALERT_EMAIL_FROM}', '${ALERT_EMAIL_TO}', msg.as_string())
    s.quit()
except Exception as e:
    print(f'email failed: {e}')
" >> "$LOG" 2>&1
    fi
}

PREV_STATE_DIR="/tmp/birmas_prev_state"
mkdir -p "$PREV_STATE_DIR"

_was_failing() { [ -f "$PREV_STATE_DIR/$1" ]; }
_mark_failing() { touch "$PREV_STATE_DIR/$1"; }
_mark_ok()      { rm -f "$PREV_STATE_DIR/$1"; }

check() {
    # Usage: check <key> <alert_msg> <recovery_msg> <condition_cmd>
    local key="$1" alert_msg="$2" recovery_msg="$3"
    shift 3
    if ! "$@" > /dev/null 2>&1; then
        if ! _was_failing "$key"; then
            _mark_failing "$key"
            send_alert "$key" "$alert_msg"
        else
            # Still failing — re-alert respecting cooldown
            send_alert "$key" "$alert_msg"
        fi
        return 1
    else
        if _was_failing "$key"; then
            _mark_ok "$key"
            send_recovery "$key" "$recovery_msg"
        fi
        return 0
    fi
}

ALL_OK=true

# ── Service checks ────────────────────────────────────────────────────────────
if ! systemctl is-active --quiet backend; then
    ALL_OK=false
    systemctl restart backend 2>/dev/null
    check "backend" "Backend service is DOWN (auto-restart attempted)" "Backend is back online" \
        systemctl is-active --quiet backend
else
    _mark_ok "backend"
fi

check "nginx"     "nginx not responding — dashboard unreachable" "nginx is back online" \
    curl -sk -o /dev/null --max-time 5 https://localhost/dashboard || ALL_OK=false

check "mediamtx"  "MediaMTX not responding — live stream may be down" "MediaMTX is back online" \
    curl -s -o /dev/null --max-time 5 http://localhost:9997/v3/paths/list || ALL_OK=false

check "hls"       "HLS stream cam1 unavailable — live feed is broken" "HLS stream cam1 is back" \
    curl -s -o /dev/null --max-time 5 http://localhost:8888/cam1/index.m3u8 || ALL_OK=false

check "postgres"  "PostgreSQL not responding — events cannot be saved" "PostgreSQL is back online" \
    bash -c "PGPASSWORD=B1rm4sC4m3r4 psql -U birmas_user -h localhost -d birmas -c 'SELECT 1'" || ALL_OK=false

# ── Pi connectivity ───────────────────────────────────────────────────────────
check "pi"        "Pi (10.0.0.2) is unreachable via WireGuard — no stream or inference" \
    "Pi (10.0.0.2) is reachable again" \
    ping -c 1 -W 3 10.0.0.2 || ALL_OK=false

# ── Disk space ────────────────────────────────────────────────────────────────
DISK_PCT=$(df / --output=pcent | tail -1 | tr -d '% ')
if [ "$DISK_PCT" -gt 85 ]; then
    ALL_OK=false
    check "disk" "Disk usage is at ${DISK_PCT}% — clean up frames or logs soon" \
        "Disk usage back below 85% (now ${DISK_PCT}%)" \
        false
else
    _mark_ok "disk"
fi

# ── RAM check (alert if available < 200MB) ────────────────────────────────────
AVAIL_MB=$(free -m | awk '/^Mem:/{print $7}')
if [ "$AVAIL_MB" -lt 200 ]; then
    ALL_OK=false
    check "ram" "Low RAM: only ${AVAIL_MB}MB available — consider restarting services" \
        "RAM recovered: ${AVAIL_MB}MB available" \
        false
else
    _mark_ok "ram"
fi

# ── Swap check (alert if swap >90% full) ─────────────────────────────────────
SWAP_TOTAL=$(free -m | awk '/^Swap:/{print $2}')
SWAP_USED=$(free -m  | awk '/^Swap:/{print $3}')
if [ "$SWAP_TOTAL" -gt 0 ] && [ $(( SWAP_USED * 100 / SWAP_TOTAL )) -gt 90 ]; then
    check "swap" "Swap is ${SWAP_USED}MB/${SWAP_TOTAL}MB — system is under memory pressure" \
        "Swap usage normalized" false
else
    _mark_ok "swap"
fi

if $ALL_OK; then
    echo "[$NOW] OK - all checks passed" >> "$LOG"
fi

# ── Rotate log (keep last 2000 lines) ────────────────────────────────────────
tail -2000 "$LOG" > "${LOG}.tmp" && mv "${LOG}.tmp" "$LOG"

