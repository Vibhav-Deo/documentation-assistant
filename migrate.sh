#!/bin/bash
set -e

echo "🔄 Running database migrations..."
docker compose exec -T api python /app/migrate.py
echo "✅ Migrations completed"
