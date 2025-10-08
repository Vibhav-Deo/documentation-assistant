#!/bin/bash

echo "🚀 Starting services..."
docker compose up -d postgres redis

echo "⏳ Waiting for services to be ready..."
sleep 10

echo "🌱 Creating seed data..."
cd api && python seed_data.py

echo "✅ Seed data created successfully!"
echo ""
echo "📋 You can now login with:"
echo "Demo User: demo@example.com / demo123 (Enterprise - Unlimited)"
echo "Admin User: admin@acmecorp.com / admin123 (Pro - 10K requests)"
echo "Regular User: user@acmecorp.com / user123 (Pro - 10K requests)"