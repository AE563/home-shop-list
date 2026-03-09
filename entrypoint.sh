#!/bin/sh
set -e

# Wait for PostgreSQL before running migrations (no-op for SQLite)
DB_ENGINE="${DB_ENGINE:-django.db.backends.sqlite3}"
if [ "$DB_ENGINE" != "django.db.backends.sqlite3" ]; then
    echo "==> Waiting for database..."
    until python -c "
import os, psycopg2
psycopg2.connect(
    host=os.environ.get('DB_HOST', 'db'),
    port=os.environ.get('DB_PORT', '5432'),
    dbname=os.environ['DB_NAME'],
    user=os.environ['DB_USER'],
    password=os.environ['DB_PASSWORD'],
)
" 2>/dev/null; do
        echo "   not ready, retrying in 1s..."
        sleep 1
    done
    echo "   database ready."
fi

python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec daphne -b 0.0.0.0 -p 8000 config.asgi:application
