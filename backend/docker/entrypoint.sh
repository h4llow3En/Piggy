#!/bin/bash

set -e

echo -n "Waiting for database ($POSTGRES_SERVER:$POSTGRES_PORT)..."

while ! nc -z "$POSTGRES_SERVER" "$POSTGRES_PORT"; do
  sleep 1
done

echo "Database is ready!"

echo "Running database migrations..."
export PYTHONPATH=$PYTHONPATH:.
alembic upgrade head

echo "Starting FastAPI application..."
exec hypercorn piggy:app --bind 0.0.0.0:8000 -w 1