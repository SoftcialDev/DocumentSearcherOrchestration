#!/bin/bash

# Start VPN in background
echo "Starting VPN connection..."
#openfortivpn &
echo "VPN startup skipped"

# Wait for VPN to establish
sleep 10  # Adjust this if your VPN takes longer to connect

if [[ "${RUN_VECTORIZER}" == "1" ]]; then
  echo "Starting vectorizer proccess..."
  # PYTHONUNBUFFERED is already set in your Dockerfile; -u is optional
  python -u /app/main.py &
fi

# Start your Gunicorn app
echo "Starting Gunicorn..."
exec gunicorn -c gunicorn.conf.py main:app
