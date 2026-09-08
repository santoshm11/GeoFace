#!/bin/bash
set -e

echo "Running migrations..."
python manage.py migrate

# Load initial data if DB is empty
if ! python manage.py shell -c "from django.contrib.auth.models import User; exit(User.objects.exists())" 2>/dev/null; then
    echo "Database appears empty. Loading initial data from data.json..."
    python manage.py loaddata data.json
else
    echo "Database already contains data. Skipping load."
fi

echo "Collecting static files..."
python manage.py collectstatic --noinput

if [ -n "$NGROK_AUTHTOKEN" ]; then
    echo "Authenticating ngrok..."
    ngrok authtoken "$NGROK_AUTHTOKEN"
fi

echo "Starting Daphne on port 9000..."
daphne -b 0.0.0.0 -p 9000 config.asgi:application &
DAPHNE_PID=$!

sleep 2

echo "Starting ngrok..."
ngrok http --domain=filler-copilot-cactus.ngrok-free.dev 9000 &
NGROK_PID=$!

trap "kill $DAPHNE_PID $NGROK_PID 2>/dev/null; wait" SIGTERM SIGINT
wait