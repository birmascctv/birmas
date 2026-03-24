#!/bin/bash
# Daily PostgreSQL backup for Birmas
BACKUP_DIR="/root/birmas/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="birmas_${TIMESTAMP}.sql.gz"

PGPASSWORD=B1rm4sC4m3r4 pg_dump -U birmas_user -h localhost birmas | gzip > "${BACKUP_DIR}/${FILENAME}"

# Keep only last 7 daily backups
ls -t "${BACKUP_DIR}"/birmas_*.sql.gz 2>/dev/null | tail -n +8 | xargs -r rm

echo "[$(date)] Backup created: ${FILENAME}" >> "${BACKUP_DIR}/backup.log"
