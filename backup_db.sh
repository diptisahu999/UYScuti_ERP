#!/bin/bash

# Configuration
BACKUP_DIR="/var/lib/odoo/backups" # Adjust this path on the host as needed
CONTAINER_NAME="uy_scuti-db-1"       # Docker container name for the DB service
DB_USER="odoo19"
DB_NAME="UY_SCUTI"
KEEP_DAYS=15

# Date format for the backup filename
DATE=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_backup_${DATE}.dump"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo "Starting database backup for ${DB_NAME}..."

# Execute pg_dump inside the docker container (custom format -F c)
# Note: -i is used instead of -t to avoid TTY output corruption for binary files
docker exec -i -e PGPASSWORD=root "$CONTAINER_NAME" pg_dump -U "$DB_USER" -F c -d "$DB_NAME" > "$BACKUP_FILE"

# Check if the backup was successful
if [ $? -eq 0 ]; then
    echo "Backup completed successfully: ${BACKUP_FILE}"
else
    echo "Error: Database backup failed!"
    exit 1
fi

# Delete backups older than KEEP_DAYS
echo "Cleaning up backups older than ${KEEP_DAYS} days..."
find "$BACKUP_DIR" -type f -name "${DB_NAME}_backup_*.dump" -mtime +$KEEP_DAYS -exec rm {} \;

echo "Backup process finished."
