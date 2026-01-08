#!/bin/sh

# Wait for database if needed (optional since we use Supabase)
# echo "Waiting for postgres..."
# while ! nc -z $DB_HOST $DB_PORT; do
#   sleep 0.1
# done

# Force IPv4 resolution for Supabase (fix for 'Network is unreachable' on IPv6)
echo "Resolving DB host to IPv4..."
DB_HOST="db.ncvvedhylfkevpbkorvd.supabase.co"
DB_IP=$(python -c "import socket; print(socket.gethostbyname('$DB_HOST'))")
if [ ! -z "$DB_IP" ]; then
    echo "Adding $DB_IP $DB_HOST to /etc/hosts"
    echo "$DB_IP $DB_HOST" >> /etc/hosts
fi

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Start server
echo "Starting server..."
exec "$@"
