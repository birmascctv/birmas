#!/bin/bash
# Sync Pi logs to server over WireGuard for centralized log viewing.
# Frames are NOT synced here — they live on the Pi SD card (1-year retention).
# For frame backup, plug a USB drive into the Pi and use pi_frame_cleanup.sh,
# or download manually via: scp -r birmas1@10.0.0.2:~/birmas/storage/frames/ ./
LOG="/root/birmas/logs/sync_pi.log"
NOW=$(date '+%Y-%m-%d %H:%M:%S')

mkdir -p /root/birmas/logs/pi

# Sync Pi logs (small — a few MB/day at most)
if rsync -az --timeout=30 birmas1@10.0.0.2:~/birmas/logs/ /root/birmas/logs/pi/ 2>/dev/null; then
    echo "[$NOW] OK - Pi logs synced" >> "$LOG"
else
    echo "[$NOW] WARN - Pi log sync failed (Pi may be offline)" >> "$LOG"
fi

# Rotate log
tail -500 "$LOG" > "${LOG}.tmp" && mv "${LOG}.tmp" "$LOG"
