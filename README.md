# Enterprise Confluence RAG with Ollama

A production-ready Retrieval-Augmented Generation (RAG) system with enterprise authentication, multi-tenancy, and comprehensive analytics. Index Confluence documentation or public URLs and get AI-powered answers using Ollama.

## 🚀 Features

### Core Features
- 🔍 **Dynamic Document Indexing**: Sync Confluence spaces or public URLs
- 🤖 **AI-Powered Q&A**: Multi-model support with conversation memory
- ⚡ **Smart Search**: Semantic, keyword, and hybrid search modes
- 📊 **Real-time Analytics**: Usage metrics and performance insights
- 🔒 **Enterprise Security**: JWT authentication, data encryption, RBAC

### Enterprise Features
- 👥 **Multi-Tenancy**: Complete data isolation between organizations
- 🏢 **User Management**: Admin/User roles with quota management
- 📈 **Organization Analytics**: Usage tracking and user metrics
- 🔐 **Authentication**: Email/password + OAuth (Google/Microsoft)
- 💾 **Production Stack**: PostgreSQL, Redis, monitoring with Prometheus/Grafana

## 🛠️ Quick Start

### Prerequisites

- Docker and Docker Compose
- Ollama running locally (install from https://ollama.ai)
- 8GB+ RAM recommended

### 1. Clone Repository
```bash
git clone https://github.com/your-repo/documentation-assistant.git
cd documentation-assistant
```

### 2. Install Ollama Models
```bash
# Install required models
ollama pull mistral
ollama pull llama2
ollama pull codellama

# Verify Ollama is running
curl http://localhost:11434/api/tags
```

### 3. Start Services
```bash
# Start all services
./start.sh

# Or manually:
docker compose up -d
```

### 4. Create Seed Data
```bash
# Create demo users and organizations
./init-seed.sh
```

### 5. Access Application
- **UI**: http://localhost:8501
- **API**: http://localhost:4000
- **API Docs**: http://localhost:4000/docs
- **Grafana**: http://localhost:3000 (admin/admin)
- **Qdrant**: http://localhost:6333/dashboard

## 👤 Demo Accounts

After running `./init-seed.sh`:

| Email | Password | Role | Plan | Quota |
|-------|----------|------|------|-------|
| demo@example.com | demo123 | User | Enterprise | Unlimited |
| admin@acmecorp.com | admin123 | Admin | Pro | 10,000/month |
| user@acmecorp.com | user123 | User | Pro | 10,000/month |

## 📖 Usage Guide

### 1. Login & Registration
- Create new organization or login with demo accounts
- Admins can view organization metrics and manage users
- Users can ask questions within their quota limits

### 2. Document Syncing (Optional)
- **Confluence**: Enter base URL, username, and API token
- **Public URLs**: Enter any public documentation URL
- Documents are isolated per organization

### 3. AI Chat Interface
- Ask questions with or without synced documents
- Choose from multiple AI models (Mistral, Llama2, CodeLlama)
- Select search type: Semantic, Keyword, or Hybrid
- Conversation memory maintains context

### 4. Admin Features
- View organization users and their usage
- Monitor API request metrics and quotas
- Access system health and performance data

## 🔧 API Reference

### Authentication
```bash
# Register new organization
POST /auth/register
{
  "email": "admin@company.com",
  "password": "secure123",
  "name": "John Admin",
  "organization_name": "My Company"
}

# Login
POST /auth/login
{
  "email": "admin@company.com",
  "password": "secure123"
}
```

### Document Sync (Authenticated)
```bash
POST /sync
Authorization: Bearer <token>
{
  "source_type": "confluence",
  "space_key_or_url": "SPACE",
  "confluence_base_url": "https://company.atlassian.net/wiki",
  "confluence_username": "user@company.com",
  "confluence_api_token": "your_api_token"
}
```

### AI Chat (Authenticated)
```bash
POST /ask
Authorization: Bearer <token>
{
  "question": "How do I deploy the application?",
  "model": "mistral",
  "max_results": 5,
  "search_type": "hybrid",
  "session_id": "optional_session_id"
}
```

### Admin Endpoints
- `GET /monitoring/organization` - Organization metrics (Admin only)
- `GET /monitoring/requests` - Request analytics (Admin only)
- `GET /monitoring/alerts` - System alerts (Admin only)
- `GET /health` - System health check
- `GET /metrics` - Prometheus metrics

## ⚙️ Configuration

### Environment Variables

Create `.env` file (copy from `.env.example`):

```bash
# Database
DATABASE_URL=postgresql://postgres:password@postgres:5432/confluence_rag

# Redis
REDIS_URL=redis://redis:6379

# JWT Security
JWT_SECRET=your-super-secret-jwt-key-change-in-production

# Ollama
OLLAMA_API_URL=http://host.docker.internal:11434/api/generate

# Vector Database
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# OAuth (Optional)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
MICROSOFT_CLIENT_ID=your_microsoft_client_id
MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret
```

### User Configuration (Via UI)
- **Organization Settings**: Plan type, quota limits
- **Document Sources**: Confluence or Public URLs
- **AI Models**: Mistral, Llama2, CodeLlama
- **Search Types**: Semantic, Keyword, Hybrid

## 🏗️ Architecture

### Services
- **API**: FastAPI backend with JWT authentication
- **UI**: Streamlit frontend with modern chat interface
- **Database**: PostgreSQL for user data and audit logs
- **Cache**: Redis for session and query caching
- **Vector DB**: Qdrant for document embeddings
- **Monitoring**: Prometheus + Grafana for metrics
- **AI**: Ollama for local LLM inference

### Security Features
- ✅ JWT-based authentication with role-based access
- ✅ AES-256 encryption for sensitive data
- ✅ Organization-level data isolation
- ✅ SSRF protection and input validation
- ✅ Audit logging for all user actions
- ✅ Non-root Docker containers

### Performance Features
- ⚡ Redis caching for faster responses
- ⚡ Optimized vector search with hybrid modes
- ⚡ Efficient document chunking and embedding
- ⚡ Connection pooling and async operations
- ⚡ Prometheus metrics for monitoring

## 🚀 Production Deployment

### Docker Compose (Recommended)
```bash
# Production deployment
docker compose -f docker-compose.yml up -d

# Scale services
docker compose up -d --scale api=3 --scale ui=2
```

### Manual Deployment
```bash
# API
cd api
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 4000

# UI
cd ui
pip install -r requirements.txt
streamlit run app.py --server.port 8501
```

### Health Checks
- API Health: `GET /health`
- Database: Check PostgreSQL connection
- Vector DB: Check Qdrant dashboard
- AI Models: Verify Ollama models loaded

## 🧪 Development

### Local Development
```bash
# Start dependencies
docker compose up -d postgres redis qdrant

# Run API locally
cd api
pip install -r requirements.txt
uvicorn main:app --reload --port 4000

# Run UI locally
cd ui
pip install -r requirements.txt
streamlit run app.py --server.port 8501
```

### Testing
```bash
# Test authentication
curl -X POST http://localhost:4000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@acmecorp.com", "password": "admin123"}'

# Test with authentication
curl -X POST http://localhost:4000/ask \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"question": "How does authentication work?", "model": "mistral"}'
```

### Database Management
```bash
# Access PostgreSQL
docker exec -it documentation-assistant-postgres-1 psql -U postgres -d confluence_rag

# View tables
\dt

# Check users
SELECT email, name, role FROM users;
```

## 🔧 Troubleshooting

### Common Issues

1. **Authentication Issues**:
   ```bash
   # Check if seed data exists
   curl http://localhost:4000/debug/users
   
   # Recreate seed data
   ./init-seed.sh
   ```

2. **Ollama Connection Failed**:
   ```bash
   # Check Ollama status
   ollama list
   curl http://localhost:11434/api/tags
   
   # Pull required models
   ollama pull mistral
   ```

3. **Database Connection Issues**:
   ```bash
   # Check PostgreSQL
   docker compose logs postgres
   
   # Reset database
   docker compose down -v
   docker compose up -d
   ```

4. **No Search Results**:
   - Login first, then sync documents
   - Check Qdrant: http://localhost:6333/dashboard
   - Verify organization isolation

### Logs & Monitoring
```bash
# View logs
docker compose logs -f api
docker compose logs -f ui

# Check system metrics
curl http://localhost:4000/health
curl http://localhost:4000/metrics

# Access Grafana dashboards
open http://localhost:3000
```

## 📊 Monitoring & Analytics

### Grafana Dashboards
- **System Overview**: CPU, memory, disk usage
- **API Metrics**: Request rates, response times, error rates
- **User Analytics**: Active users, popular queries
- **Database Performance**: Connection pools, query performance

### Organization Analytics
- User request counts and quotas
- Document sync statistics
- Search performance metrics
- Audit trail and security events

## 🔄 Backup & Recovery

```bash
# Backup PostgreSQL
docker exec documentation-assistant-postgres-1 pg_dump -U postgres confluence_rag > backup.sql

# Backup Qdrant data
tar -czf qdrant_backup.tar.gz qdrant_data/

# Restore PostgreSQL
docker exec -i documentation-assistant-postgres-1 psql -U postgres confluence_rag < backup.sql
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

- 📖 Documentation: Check this README and API docs
- 🐛 Issues: Create GitHub issues for bugs
- 💬 Discussions: Use GitHub discussions for questions
- 📧 Contact: [your-email@domain.com]

---

**Built with ❤️ using FastAPI, Streamlit, Ollama, and modern DevOps practices.**