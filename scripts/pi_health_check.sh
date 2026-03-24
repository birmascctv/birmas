#!/bin/bash
LOG=/home/birmas1/birmas/logs/pi_health.log
mkdir -p /home/birmas1/birmas/logs

ISSUES=""
# Check services — treat "activating" as OK (service is starting up)
for svc in ffmpeg-publisher inference wg-quick@wg0; do
    STATE=$(systemctl is-active $svc 2>/dev/null)
    if [ "$STATE" != "active" ] && [ "$STATE" != "activating" ]; then
        ISSUES="$ISSUES $svc-down"
    fi
done

# Check WireGuard tunnel
if ! ping -c 1 -W 3 10.0.0.1 > /dev/null 2>&1; then
    ISSUES="$ISSUES wireguard-unreachable"
fi

# Check camera reachable
if ! ping -c 1 -W 3 192.168.68.101 > /dev/null 2>&1; then
    ISSUES="$ISSUES camera-unreachable"
fi

# Check disk (warn >80%)
DISK_PCT=$(df / | awk 'NR==2{gsub("%",""); print $5}')
if [ "$DISK_PCT" -gt 80 ]; then
    ISSUES="$ISSUES disk-${DISK_PCT}pct"
fi

TS=$(date '+%Y-%m-%d %H:%M:%S')
if [ -z "$ISSUES" ]; then
    echo "[$TS] OK - all checks passed" >> $LOG
else
    echo "[$TS] ALERT:$ISSUES" >> $LOG
fi

# Keep log under 500 lines
tail -500 $LOG > /tmp/pi_health.tmp && mv /tmp/pi_health.tmp $LOG
