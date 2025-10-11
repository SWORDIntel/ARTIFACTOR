# ARTIFACTOR Docker Configurations

## Overview

This directory contains Docker and Docker Compose configurations for ARTIFACTOR v3.0 deployment.

## Available Configurations

### 1. backend-compose.yml (New - Simplified)
**Purpose**: Backend services only for Chrome Extension integration

**Services**:
- PostgreSQL 15 (Port 5432)
- Redis 7 (Port 6379)
- FastAPI Backend API (Port 8000)

**Use Case**:
- Chrome Extension development
- Minimal backend deployment
- API-only applications

**Quick Start**:
```bash
# Using management script (recommended)
./docker/backend-services.sh start

# Or using docker-compose directly
docker-compose -f docker/backend-compose.yml up -d
```

**Documentation**: `BACKEND_SETUP.md`

---

### 2. docker-compose.yml (Full Stack - Development)
**Purpose**: Complete development environment

**Services**:
- PostgreSQL 15
- Redis 7
- FastAPI Backend
- React Frontend (Port 3000)
- Nginx Reverse Proxy (Port 80/443)
- Agent Bridge (v2.0 compatibility)

**Use Case**:
- Full-stack development
- Frontend + Backend testing
- Local integration testing

**Quick Start**:
```bash
docker-compose up -d
```

---

### 3. docker-compose.secure.yml (Production)
**Purpose**: Security-hardened production deployment

**Features**:
- Security hardening (read-only filesystems, restricted capabilities)
- Resource limits and reservations
- Health checks and monitoring
- TLS/SSL support
- Secrets management
- Audit logging

**Use Case**:
- Production deployments
- Security-critical environments
- Enterprise deployments

**Quick Start**:
```bash
docker-compose -f docker/docker-compose.secure.yml up -d
```

**Documentation**: `../docs/PRODUCTION_DEPLOYMENT_GUIDE.md`

---

## Configuration Comparison

| Feature | backend-compose.yml | docker-compose.yml | docker-compose.secure.yml |
|---------|--------------------|--------------------|---------------------------|
| PostgreSQL | ✓ | ✓ | ✓ (Hardened) |
| Redis | ✓ | ✓ | ✓ (Hardened) |
| Backend API | ✓ | ✓ | ✓ (Hardened) |
| Frontend | ✗ | ✓ | ✓ (Hardened) |
| Nginx | ✗ | ✓ (Profile) | ✓ (TLS) |
| Agent Bridge | ✗ | ✓ (Profile) | ✓ |
| Chrome Extension CORS | ✓ | ✗ | ✗ |
| Security Hardening | Basic | Medium | Maximum |
| Resource Limits | ✓ | ✓ | ✓ Enhanced |
| Health Checks | ✓ | ✓ | ✓ Enhanced |
| Suitable For | Extension Dev | Full Dev | Production |

---

## Management Scripts

### backend-services.sh
Simplified management interface for backend services.

**Commands**:
```bash
./docker/backend-services.sh start      # Start services
./docker/backend-services.sh stop       # Stop services
./docker/backend-services.sh restart    # Restart services
./docker/backend-services.sh status     # Show status
./docker/backend-services.sh logs       # View logs
./docker/backend-services.sh validate   # Run tests
./docker/backend-services.sh backup     # Create backup
./docker/backend-services.sh shell <svc> # Open shell
./docker/backend-services.sh clean      # Remove all data
```

### validate-backend-services.sh
Comprehensive validation and health checking.

**Tests**:
- Docker Compose configuration
- Environment variables
- Container status and health
- Service connectivity
- Database connections
- API endpoints
- Network configuration
- CORS settings

**Usage**:
```bash
./docker/validate-backend-services.sh
```

---

## Quick Reference

### Start Backend Services (Recommended Method)
```bash
cd /home/john/ARTIFACTOR
./docker/backend-services.sh start
```

### Check Status
```bash
./docker/backend-services.sh status
```

### View Logs
```bash
# All services
./docker/backend-services.sh logs

# Specific service
./docker/backend-services.sh logs backend
```

### Validate Health
```bash
./docker/validate-backend-services.sh
```

### Create Backup
```bash
./docker/backend-services.sh backup
```

### Access Database Shell
```bash
./docker/backend-services.sh shell postgres
```

### Access Redis CLI
```bash
./docker/backend-services.sh shell redis
```

### Access Backend Shell
```bash
./docker/backend-services.sh shell backend
```

---

## Environment Configuration

### Required Variables (.env)
```bash
# Database
POSTGRES_DB=artifactor_v3
POSTGRES_USER=artifactor
POSTGRES_PASSWORD=<secure_password>

# Security
SECRET_KEY=<256_bit_key>

# Optional
DEBUG=false
ML_CLASSIFICATION_ENABLED=true
SEMANTIC_SEARCH_ENABLED=true
COLLABORATION_ENABLED=true
PLUGIN_SYSTEM_ENABLED=true
METRICS_ENABLED=true
AUDIT_LOGGING_ENABLED=true
```

### Generate Secure Credentials
```bash
# Secret key (256-bit)
openssl rand -hex 32

# Database password
openssl rand -base64 32

# Or use the management script (auto-generates)
./docker/backend-services.sh start
```

---

## Port Mappings

| Service | Container Port | Host Port | Purpose |
|---------|---------------|-----------|---------|
| Backend API | 8000 | 8000 | REST API |
| PostgreSQL | 5432 | 5432 | Database |
| Redis | 6379 | 6379 | Cache |
| Frontend | 3000 | 3000 | Web UI (full stack) |
| Nginx | 80/443 | 80/443 | Reverse Proxy (full stack) |

---

## Volume Management

### Backend Services Volumes
- `artifactor_backend_postgres_data` - PostgreSQL data
- `artifactor_backend_redis_data` - Redis persistence
- `artifactor_backend_upload_data` - Uploaded artifacts

### List Volumes
```bash
docker volume ls | grep artifactor_backend
```

### Inspect Volume
```bash
docker volume inspect artifactor_backend_postgres_data
```

### Backup Volumes
```bash
./docker/backend-services.sh backup
```

### Remove Volumes (DESTRUCTIVE!)
```bash
docker-compose -f docker/backend-compose.yml down -v
```

---

## Troubleshooting

### Services Won't Start
```bash
# Check Docker daemon
systemctl status docker

# Check logs
./docker/backend-services.sh logs

# Validate configuration
docker-compose -f docker/backend-compose.yml config
```

### Port Conflicts
```bash
# Check what's using ports
sudo netstat -tlnp | grep -E '8000|5432|6379'

# Or use ss
ss -tlnp | grep -E '8000|5432|6379'

# Kill conflicting processes or change ports in backend-compose.yml
```

### Database Connection Issues
```bash
# Test connection
docker exec artifactor_backend_postgres psql -U artifactor -d artifactor_v3 -c "SELECT 1;"

# Check credentials
docker exec artifactor_backend_postgres env | grep POSTGRES
```

### API Not Responding
```bash
# Check container logs
docker logs artifactor_backend_api --tail 100

# Check health
curl -v http://localhost:8000/api/health

# Restart service
docker-compose -f docker/backend-compose.yml restart backend
```

### CORS Issues with Chrome Extension
```bash
# Verify CORS configuration
docker exec artifactor_backend_api env | grep ALLOWED_ORIGINS

# Should include: chrome-extension://*
```

### Performance Issues
```bash
# Check resource usage
docker stats

# Adjust limits in backend-compose.yml:
deploy:
  resources:
    limits:
      memory: 2G  # Increase
      cpus: '2.0'  # Increase
```

---

## Development Workflow

### 1. Initial Setup
```bash
cd /home/john/ARTIFACTOR
./docker/backend-services.sh start
./docker/validate-backend-services.sh
```

### 2. Development Cycle
```bash
# Make code changes in ../backend/

# Rebuild and restart
docker-compose -f docker/backend-compose.yml up -d --build

# Watch logs
./docker/backend-services.sh logs backend
```

### 3. Testing
```bash
# Run validation
./docker/validate-backend-services.sh

# Access API docs
open http://localhost:8000/docs

# Test endpoints
curl http://localhost:8000/api/health
```

### 4. Cleanup
```bash
# Stop services
./docker/backend-services.sh stop

# Or remove everything
./docker/backend-services.sh clean
```

---

## Production Deployment

For production deployment, use `docker-compose.secure.yml`:

```bash
# 1. Review security configuration
cat docker/docker-compose.secure.yml

# 2. Configure secrets
./scripts/setup-secure-environment.sh

# 3. Deploy
docker-compose -f docker/docker-compose.secure.yml up -d

# 4. Validate
./scripts/health-check.sh

# 5. Monitor
./scripts/performance-optimizer.sh
```

See: `../docs/PRODUCTION_DEPLOYMENT_GUIDE.md`

---

## Security Considerations

### Backend Services (backend-compose.yml)
- ✓ Environment variable based configuration
- ✓ Basic resource limits
- ✓ Health checks
- ✓ Restart policies
- ✓ CORS configuration
- ⚠ Development-focused (not production-ready)

### Production Deployment (docker-compose.secure.yml)
- ✓ Read-only root filesystems
- ✓ Dropped capabilities
- ✓ Security scanning
- ✓ Secrets management
- ✓ TLS/SSL encryption
- ✓ Audit logging
- ✓ Network isolation
- ✓ Resource limits

---

## Additional Resources

### Documentation
- `BACKEND_SETUP.md` - Backend services setup guide
- `../docs/API_SECURITY_GUIDE.md` - API security best practices
- `../docs/PRODUCTION_DEPLOYMENT_GUIDE.md` - Production deployment
- `../docs/PERFORMANCE_GUIDE.md` - Performance optimization
- `../docs/TROUBLESHOOTING_GUIDE.md` - Troubleshooting guide

### Scripts
- `backend-services.sh` - Service management
- `validate-backend-services.sh` - Health validation
- `../scripts/deploy.sh` - Automated deployment
- `../scripts/health-check.sh` - Health monitoring
- `../scripts/performance-optimizer.sh` - Performance tuning

### Configuration Files
- `backend-compose.yml` - Backend services (this document)
- `docker-compose.yml` - Full development stack
- `docker-compose.secure.yml` - Production configuration
- `../backend/Dockerfile` - Backend container image
- `../frontend/Dockerfile` - Frontend container image

---

## Support

- **Repository**: https://github.com/SWORDIntel/ARTIFACTOR
- **Issues**: GitHub Issues
- **Contact**: ARTIFACTOR@swordintelligence.airforce
- **Organization**: https://swordintelligence.airforce

---

**ARTIFACTOR v3.0** - Docker Infrastructure
Created: 2025-10-11
SWORD Intelligence - Advanced AI & Software Solutions
