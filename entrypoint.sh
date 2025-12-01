#!/bin/bash
set -e

# Generate self-signed certs if they don't exist
if [ ! -f certs/cert.pem ] || [ ! -f certs/key.pem ]; then
    echo "Generating self-signed certificates..."
    openssl req -x509 -newkey rsa:4096 -nodes \
        -keyout certs/key.pem \
        -out certs/cert.pem \
        -days 365 \
        -subj "/CN=localhost"
fi

# Initialize database
echo "Initializing database..."
flask init-db

# Start the application
echo "Starting ClickFix Training Tool..."
exec python run.py