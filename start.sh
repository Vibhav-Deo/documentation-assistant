#!/bin/bash

set -e  # Exit on any error

echo "🚀 Starting Enterprise Confluence RAG with Ollama..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if Ollama is running
echo "🤖 Checking Ollama status..."
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "⚠️  Ollama is not running. Please start Ollama first:"
    echo "   1. Install Ollama: https://ollama.ai"
    echo "   2. Start Ollama: ollama serve"
    echo "   3. Install models: ollama pull mistral && ollama pull llama2"
    echo ""
    exit 1
fi

# Check if required models are available
echo "📋 Checking Ollama models..."
if ! ollama list | grep -q "mistral"; then
    echo "⚠️  Installing Mistral model..."
    ollama pull mistral
fi

echo "✅ Ollama is ready with required models"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📄 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please review and update .env file with your settings"
fi

# Stop any running services
echo "🛑 Stopping any running Docker services..."
docker compose down

# Start services
echo "🐳 Starting Docker services..."
docker compose build --no-cache
docker compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
echo "   (Database will auto-initialize on first startup)"
sleep 10

# Check service health
echo "🔍 Checking service health..."
for i in {1..30}; do
    if curl -s http://localhost:4000/health > /dev/null; then
        echo "✅ API is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "⚠️  API health check timeout. Check logs: docker compose logs api"
    fi
    sleep 2
done

echo ""
echo "✨ Services started successfully!"
echo ""
echo "📄 Access Points:"
echo "   🖥️  UI: http://localhost:8501"
echo "   🚀 API: http://localhost:4000"
echo "   📆 API Docs: http://localhost:4000/docs"
echo "   📊 Grafana: http://localhost:3000 (admin/admin)"
echo "   🔍 Qdrant: http://localhost:6333/dashboard"
echo ""
echo "👤 Demo Accounts (auto-created on first startup):"
echo "   Admin: admin@acmecorp.com / admin123"
echo "   User:  user@acmecorp.com / user123"
echo "   Demo:  demo@example.com / demo123"
echo ""
echo "💡 First-time setup:"
echo "   The database and seed data are automatically created on first startup."
echo "   Check API logs to see initialization progress: docker compose logs -f api"
echo ""
echo "📝 Useful Commands:"
echo "   View logs: docker compose logs -f"
echo "   Stop services: docker compose down"
echo "   Reset all data: docker compose down -v && ./start.sh"
echo "   Re-seed manually: docker exec -it <api-container> python3 scripts/init_database.py"