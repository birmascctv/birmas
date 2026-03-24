#!/bin/bash
# Birmas Health Check & Alerting
# Runs every 5 minutes via cron, logs issues to /root/birmas/logs/health.log
# To add Telegram alerts, set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID below

TELEGRAM_BOT_TOKEN=""
TELEGRAM_CHAT_ID=""
LOG="/root/birmas/logs/health.log"
ALERT_LOG="/root/birmas/logs/alert_sent.log"
NOW=$(date '+%Y-%m-%d %H:%M:%S')

send_alert() {
    local msg="$1"
    echo "[$NOW] ALERT: $msg" >> "$LOG"
    if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
        curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -d chat_id="$TELEGRAM_CHAT_ID" \
            -d text="🚨 Birmas Alert: $msg" \
            -d parse_mode="Markdown" > /dev/null 2>&1
    fi
}

ISSUES=""

# Check backend
if ! systemctl is-active --quiet backend; then
    ISSUES="${ISSUES}Backend service DOWN. "
    systemctl restart backend 2>/dev/null
fi

# Check nginx (static frontend)
if ! curl -sk -o /dev/null --max-time 5 https://localhost/dashboard; then
    ISSUES="${ISSUES}Nginx/frontend not responding. "
fi

# Check MediaMTX
if ! curl -s -o /dev/null --max-time 5 http://localhost:9997/v3/paths/list; then
    ISSUES="${ISSUES}MediaMTX API not responding. "
fi

# Check HLS stream
if ! curl -s -o /dev/null --max-time 5 http://localhost:8888/cam1/index.m3u8; then
    ISSUES="${ISSUES}HLS stream cam1 unavailable. "
fi

# Check database
if ! PGPASSWORD=B1rm4sC4m3r4 psql -U birmas_user -h localhost -d birmas -c "SELECT 1" > /dev/null 2>&1; then
    ISSUES="${ISSUES}PostgreSQL not responding. "
fi

# Check Pi connectivity
if ! ping -c 1 -W 3 10.0.0.2 > /dev/null 2>&1; then
    ISSUES="${ISSUES}Pi (10.0.0.2) unreachable. "
fi

# Check disk space (alert if >85%)
DISK_PCT=$(df / --output=pcent | tail -1 | tr -d '% ')
if [ "$DISK_PCT" -gt 85 ]; then
    ISSUES="${ISSUES}Disk usage at ${DISK_PCT}%. "
fi

if [ -n "$ISSUES" ]; then
    send_alert "$ISSUES"
else
    echo "[$NOW] OK - all checks passed" >> "$LOG"
fi

# Rotate health log (keep last 1000 lines)
tail -1000 "$LOG" > "${LOG}.tmp" && mv "${LOG}.tmp" "$LOG"
