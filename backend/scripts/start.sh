#!/bin/bash
set -e

# Set environment variable to prevent tokenizer deadlock warnings
export TOKENIZERS_PARALLELISM=false

# Wait for PostgreSQL to be ready (parsing host and port dynamically from DATABASE_URL)
DB_HOST="db"
DB_PORT="5432"

if [ -n "$DATABASE_URL" ]; then
    # Remove everything up to //
    TEMP="${DATABASE_URL#*//}"
    # Remove path (everything after first /)
    TEMP="${TEMP%%/*}"
    # Extract host:port (everything after @ if present)
    case "$TEMP" in
        *@*) HOST_PORT="${TEMP#*@}" ;;
        *) HOST_PORT="$TEMP" ;;
    esac
    # Extract host and port
    case "$HOST_PORT" in
        *:*)
            DB_HOST="${HOST_PORT%%:*}"
            DB_PORT="${HOST_PORT##*:}"
            ;;
        *)
            DB_HOST="$HOST_PORT"
            DB_PORT="5432"
            ;;
    esac
fi

echo "Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."
while ! nc -z "$DB_HOST" "$DB_PORT"; do
  sleep 0.1
done
echo "PostgreSQL is ready!"

# Check if Firebase credentials exist, but don't create them if missing
if [ ! -z "$FIREBASE_CREDENTIALS" ] && [ ! -f "$FIREBASE_CREDENTIALS" ]; then
    echo "Warning: Firebase credentials file not found at $FIREBASE_CREDENTIALS. Continuing without Firebase credentials..."
fi



# Preload embedding models to avoid runtime issues
echo "Preloading embedding models..."
python scripts/preload_models.py
if [ $? -eq 0 ]; then
    echo "Models preloaded successfully!"
else
    echo "Warning: Model preloading failed. Continuing anyway..."
fi

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Use only 2 workers to reduce resource usage and database connection issues
WORKERS=${WORKERS:-1}

# Start the application with Gunicorn
echo "Starting FastAPI application with Gunicorn ($WORKERS workers)..."
gunicorn app.main:app \
    --workers $WORKERS \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --keep-alive 5 \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    --preload