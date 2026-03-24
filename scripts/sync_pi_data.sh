#!/bin/bash
# Sync Pi logs and frame backups to server over WireGuard
LOG="/root/birmas/logs/sync_pi.log"
NOW=$(date '+%Y-%m-%d %H:%M:%S')

mkdir -p /root/birmas/logs/pi /root/birmas/backups/frames

# Sync Pi logs
if rsync -az --timeout=30 birmas1@10.0.0.2:~/birmas/logs/ /root/birmas/logs/pi/ 2>/dev/null; then
    echo "[$NOW] OK - Pi logs synced" >> "$LOG"
else
    echo "[$NOW] WARN - Pi log sync failed (Pi may be offline)" >> "$LOG"
fi

# Sync Pi frames as backup
if rsync -az --timeout=60 birmas1@10.0.0.2:~/birmas/storage/frames/ /root/birmas/backups/frames/ 2>/dev/null; then
    FRAME_COUNT=$(ls /root/birmas/backups/frames/ 2>/dev/null | wc -l)
    echo "[$NOW] OK - Pi frames synced ($FRAME_COUNT files)" >> "$LOG"
else
    echo "[$NOW] WARN - Pi frame sync failed (Pi may be offline)" >> "$LOG"
fi

# Rotate log
tail -500 "$LOG" > "${LOG}.tmp" && mv "${LOG}.tmp" "$LOG"
