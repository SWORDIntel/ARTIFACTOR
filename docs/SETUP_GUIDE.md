# ARTIFACTOR v3.0 Setup Guide

Complete setup instructions for the web-enabled artifact management system with v2.0 compatibility.

## 🎯 Overview

ARTIFACTOR v3.0 provides three deployment options:
1. **Docker Development** (Recommended) - Complete environment with hot reloading
2. **Manual Development** - Local Python/Node.js development
3. **Production Deployment** - Optimized containers with Nginx

## 📋 Prerequisites

### Required Software
- **Docker & Docker Compose** 20.10+ (for Docker setup)
- **Python** 3.11+ (for manual backend development)
- **Node.js** 18+ with npm (for manual frontend development)
- **Git** (for cloning repository)

### System Requirements
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space for Docker images and dependencies
- **Network**: Internet access for package downloads

## 🚀 Quick Start (Docker - Recommended)

### 1. Clone and Navigate
```bash
git clone https://github.com/SWORDIntel/ARTIFACTOR.git
cd ARTIFACTOR
```

### 2. Start All Services
```bash
cd docker
docker-compose up -d
```

### 3. Verify Services
```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 4. Access Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs
- **Database**: localhost:5432 (artifactor/artifactor)

### 5. Create Admin User
```bash
# Access backend container
docker-compose exec backend python -c "
import asyncio
from backend.database import AsyncSessionLocal
from backend.models import User
from backend.routers.auth import AuthService

async def create_admin():
    async with AsyncSessionLocal() as session:
        auth_service = AuthService()
        admin = User(
            username='admin',
            email='admin@artifactor.local',
            full_name='Administrator',
            hashed_password=auth_service.hash_password('admin123'),
            is_active=True,
            is_superuser=True
        )
        session.add(admin)
        await session.commit()
        print('Admin user created: admin/admin123')

asyncio.run(create_admin())
"
```

## 🛠️ Manual Development Setup

### Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your database credentials

# Start PostgreSQL (if not using Docker)
# Ubuntu/Debian: sudo systemctl start postgresql
# Create database: createdb artifactor_v3

# Run database migrations
alembic upgrade head

# Start development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup
```bash
# Navigate to frontend directory (new terminal)
cd frontend

# Install dependencies
npm install

# Setup environment variables
cp .env.example .env
# Edit .env with your API URL

# Start development server
npm start
```

### Database Setup (Manual)
```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE artifactor_v3;
CREATE USER artifactor WITH ENCRYPTED PASSWORD 'artifactor';
GRANT ALL PRIVILEGES ON DATABASE artifactor_v3 TO artifactor;
\q

# Run initial migration
cd backend
alembic upgrade head
```

## 🔄 v2.0 Migration

### Automatic Migration
```bash
# Using Docker
docker-compose exec backend python -c "
import asyncio
from backend.migration.v2_importer import V2DataImporter
from backend.database import AsyncSessionLocal

async def migrate():
    importer = V2DataImporter('/home/john/ARTIFACTOR')
    async with AsyncSessionLocal() as session:
        artifacts = await importer.migrate_artifacts(session)
        users = await importer.migrate_users(session)
        configs = await importer.migrate_configurations(session)
        await session.commit()

        summary = importer.get_migration_summary()
        print(f'Migration Summary:')
        print(f'  Artifacts: {summary[\"imported_artifacts\"]}')
        print(f'  Users: {summary[\"imported_users\"]}')
        print(f'  Configs: {summary[\"imported_configs\"]}')
        print(f'  Errors: {summary[\"error_count\"]}')
        print(f'  Success Rate: {summary[\"success_rate\"]:.1f}%')

asyncio.run(migrate())
"
```

### Manual Migration Script
```python
# migration_script.py
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / 'backend'))

from backend.migration.v2_importer import V2DataImporter
from backend.database import AsyncSessionLocal

async def main():
    v2_path = input("Enter v2.0 ARTIFACTOR path (default: /home/john/ARTIFACTOR): ").strip()
    if not v2_path:
        v2_path = "/home/john/ARTIFACTOR"

    importer = V2DataImporter(v2_path)

    async with AsyncSessionLocal() as session:
        print("Starting migration...")

        artifacts = await importer.migrate_artifacts(session)
        print(f"Migrated {artifacts} artifacts")

        users = await importer.migrate_users(session)
        print(f"Migrated {users} users")

        configs = await importer.migrate_configurations(session)
        print(f"Migrated {configs} configurations")

        await session.commit()

        summary = importer.get_migration_summary()
        print(f"\nMigration Complete:")
        print(f"  Success Rate: {summary['success_rate']:.1f}%")
        if summary['errors']:
            print(f"  Errors: {summary['error_count']}")
            for error in summary['errors'][:5]:  # Show first 5 errors
                print(f"    - {error}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 🧪 Testing

### Run All Tests
```bash
# Backend tests
cd backend
pytest tests/ -v --cov=backend

# Frontend tests
cd frontend
npm test -- --coverage

# Integration tests
docker-compose -f docker/docker-compose.yml up -d postgres
cd backend
pytest tests/test_main.py::TestIntegration -v
```

### Test Categories
- **Unit Tests**: Individual component testing
- **Integration Tests**: API endpoint testing
- **Agent Tests**: v2.0 compatibility testing
- **Performance Tests**: Response time and throughput
- **Migration Tests**: v2.0 to v3.0 migration validation

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```bash
# Database
DATABASE_URL=postgresql://artifactor:artifactor@localhost:5432/artifactor_v3
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
DEBUG=true
HOST=0.0.0.0
PORT=8000

# v2.0 Compatibility
V2_COORDINATION_ENABLED=true
PRESERVE_V2_COMPATIBILITY=true
AGENT_BRIDGE_ENABLED=true
```

#### Frontend (.env)
```bash
# API Configuration
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_WS_URL=ws://localhost:8000/ws

# Development
REACT_APP_ENV=development
GENERATE_SOURCEMAP=true
```

### Docker Configuration
```yaml
# docker/docker-compose.override.yml (for custom settings)
version: '3.8'
services:
  backend:
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
    volumes:
      - ../logs:/app/logs  # Custom log directory

  frontend:
    environment:
      - REACT_APP_DEBUG=true
    volumes:
      - ../frontend/src:/app/src:ro  # Read-only source mapping
```

## 🚀 Production Deployment

### Production Docker Setup
```bash
# Build production images
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Start production services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Use Nginx profile for reverse proxy
docker-compose --profile production up -d
```

### Production Environment Variables
```bash
# Backend production settings
DEBUG=false
SECRET_KEY=secure-random-key-generate-new-one
DATABASE_URL=postgresql://user:pass@postgres:5432/artifactor_v3
ALLOWED_ORIGINS=["https://yourdomain.com"]

# Frontend production settings
REACT_APP_API_URL=https://yourdomain.com/api
REACT_APP_WS_URL=wss://yourdomain.com/ws
```

### SSL/HTTPS Setup
```bash
# Generate SSL certificates (Let's Encrypt example)
sudo apt install certbot
sudo certbot certonly --standalone -d yourdomain.com

# Update nginx configuration
# Copy certificates to docker/nginx/certs/
# Update docker/nginx/conf.d/default.conf
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Database Connection Failed
```bash
# Check PostgreSQL status
docker-compose logs postgres

# Verify connection
docker-compose exec postgres psql -U artifactor -d artifactor_v3 -c "SELECT 1;"

# Reset database
docker-compose down -v
docker-compose up -d postgres
```

#### 2. Agent Bridge Not Working
```bash
# Check v2.0 path detection
docker-compose exec backend python -c "
from backend.services.agent_bridge import AgentCoordinationBridge
import asyncio

async def test():
    bridge = AgentCoordinationBridge()
    await bridge.initialize()
    status = bridge.get_status()
    print(f'Bridge Status: {status}')

asyncio.run(test())
"
```

#### 3. Frontend Build Issues
```bash
# Clear npm cache
cd frontend
npm cache clean --force
rm -rf node_modules package-lock.json
npm install

# Check Node.js version
node --version  # Should be 18+
```

#### 4. Port Conflicts
```bash
# Check port usage
netstat -tlnp | grep :3000
netstat -tlnp | grep :8000

# Use different ports
export REACT_APP_PORT=3001
export BACKEND_PORT=8001
docker-compose up -d
```

### Performance Issues

#### Backend Performance
```bash
# Monitor backend performance
docker-compose exec backend python -c "
import psutil
import asyncio
from backend.services.agent_bridge import AgentCoordinationBridge

async def monitor():
    bridge = AgentCoordinationBridge()
    await bridge.initialize()

    # Test agent performance
    start = asyncio.get_event_loop().time()
    result = await bridge.invoke_agent('DEBUGGER', {'task_type': 'health_check'})
    end = asyncio.get_event_loop().time()

    print(f'Agent Response Time: {(end-start)*1000:.1f}ms')
    print(f'Memory Usage: {psutil.Process().memory_info().rss / 1024 / 1024:.1f}MB')
    print(f'CPU Usage: {psutil.cpu_percent()}%')

asyncio.run(monitor())
"
```

#### Database Performance
```bash
# Check database performance
docker-compose exec postgres psql -U artifactor -d artifactor_v3 -c "
SELECT
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats
WHERE schemaname = 'public'
ORDER BY tablename, attname;
"
```

### Log Analysis
```bash
# View application logs
docker-compose logs -f backend | grep ERROR
docker-compose logs -f frontend | grep Error

# Database logs
docker-compose logs postgres | grep ERROR

# System resource usage
docker stats artifactor_backend artifactor_frontend artifactor_postgres
```

## 📚 Additional Resources

### API Documentation
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

### Development Tools
- **Database Admin**: pgAdmin or DBeaver for PostgreSQL management
- **API Testing**: Postman collection available in `/docs/api/`
- **Code Quality**: ESLint, Prettier, Black, isort configurations included

### Monitoring
- **Health Checks**: Built-in health endpoints for all services
- **Performance Metrics**: Available via `/api/metrics` endpoint
- **Agent Monitoring**: Real-time agent status and performance tracking

### Support
- **Issues**: Report bugs via GitHub Issues
- **Documentation**: Complete docs in `/docs/` directory
- **Examples**: Sample configurations in `/examples/` directory

---

**ARTIFACTOR v3.0 is now ready for development and deployment!**

The setup provides a complete foundation for web-enabled artifact management while preserving the highly optimized v2.0 agent coordination system.