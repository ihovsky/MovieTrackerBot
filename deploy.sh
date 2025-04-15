#!/bin/bash

LOCAL_DIR="$HOME/Desktop/MovieTracker"
REMOTE_USER="root"
REMOTE_HOST="77.246.96.220"
REMOTE_DIR="/root/MovieTracker"

echo "Starting file watcher for $LOCAL_DIR..."

# Отслеживание изменений в файлах с помощью fswatch
fswatch -0 "$LOCAL_DIR" --exclude "subscriptions.db" | while read -d "" event; do
    echo "Detected change in $event. Deploying to $REMOTE_HOST..."

    # Копирование файлов на сервер
    rsync -avz --exclude 'subscriptions.db' "$LOCAL_DIR/" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/"

    # Установка зависимостей и перезапуск бота
    ssh "$REMOTE_USER@$REMOTE_HOST" "
        cd $REMOTE_DIR &&
        pip3 install -r requirements.txt &&
        systemctl restart movietracker
    "

    echo "Deploy completed."
done