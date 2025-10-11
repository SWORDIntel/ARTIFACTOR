# ARTIFACTOR Backend Services Setup

## Overview

This simplified Docker Compose configuration provides backend services only for ARTIFACTOR v3.0, optimized for Chrome Extension integration.

## Services Included

- **PostgreSQL 15**: Database (Port 5432)
- **Redis 7**: Cache server (Port 6379)
- **FastAPI Backend**: REST API (Port 8000)

## Prerequisites

1. Docker Engine 20.10+
2. Docker Compose 2.0+
3. `.env` file in project root with required variables

## Quick Start

### 1. Environment Setup

Create `.env` file in `/home/john/ARTIFACTOR/` with:

```bash
# Database Configuration
POSTGRES_DB=artifactor_v3
POSTGRES_USER=artifactor
POSTGRES_PASSWORD=your_secure_password_here

# Security
SECRET_KEY=your_256_bit_secret_key_here

# Optional Configuration
DEBUG=false
ML_CLASSIFICATION_ENABLED=true
SEMANTIC_SEARCH_ENABLED=true
COLLABORATION_ENABLED=true
PLUGIN_SYSTEM_ENABLED=true
METRICS_ENABLED=true
AUDIT_LOGGING_ENABLED=true
```

**Generate secure credentials:**
```bash
# Secret Key (256-bit)
openssl rand -hex 32

# PostgreSQL Password
openssl rand -base64 32
```

### 2. Start Backend Services

```bash
# Start all services
docker-compose -f docker/backend-compose.yml up -d

# View logs
docker-compose -f docker/backend-compose.yml logs -f

# Check service health
docker-compose -f docker/backend-compose.yml ps
```

### 3. Verify Services

**Check API Health:**
```bash
curl http://localhost:8000/api/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "version": "3.0.0"
}
```

**Test Database Connection:**
```bash
docker exec artifactor_backend_postgres psql -U artifactor -d artifactor_v3 -c "SELECT version();"
```

**Test Redis Connection:**
```bash
docker exec artifactor_backend_redis redis-cli ping
# Expected: PONG
```

### 4. API Documentation

Once running, access interactive API docs:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Chrome Extension Integration

### CORS Configuration

The backend is pre-configured to accept requests from:
- `http://localhost:3000` (Frontend development)
- `http://127.0.0.1:3000` (Alternative localhost)
- `chrome-extension://*` (All Chrome extensions)

### Extension API Usage

**1. Authentication:**
```javascript
// From Chrome extension content script
const response = await fetch('http://localhost:8000/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'user',
    password: 'password'
  })
});
const { access_token } = await response.json();
```

**2. Upload Artifact:**
```javascript
const formData = new FormData();
formData.append('file', artifactBlob, 'artifact.py');
formData.append('metadata', JSON.stringify({
  title: 'My Artifact',
  type: 'code',
  language: 'python'
}));

const response = await fetch('http://localhost:8000/api/artifacts', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`
  },
  body: formData
});
```

## Service Management

### Start Services
```bash
docker-compose -f docker/backend-compose.yml up -d
```

### Stop Services
```bash
docker-compose -f docker/backend-compose.yml down
```

### Restart Services
```bash
docker-compose -f docker/backend-compose.yml restart
```

### Stop and Remove Data
```bash
# WARNING: This deletes all data!
docker-compose -f docker/backend-compose.yml down -v
```

### View Logs
```bash
# All services
docker-compose -f docker/backend-compose.yml logs -f

# Specific service
docker-compose -f docker/backend-compose.yml logs -f backend
```

### Service Status
```bash
docker-compose -f docker/backend-compose.yml ps
```

## Performance Monitoring

### Resource Usage
```bash
docker stats artifactor_backend_postgres artifactor_backend_redis artifactor_backend_api
```

### Database Performance
```bash
# Connection count
docker exec artifactor_backend_postgres psql -U artifactor -d artifactor_v3 -c "SELECT count(*) FROM pg_stat_activity;"

# Database size
docker exec artifactor_backend_postgres psql -U artifactor -d artifactor_v3 -c "SELECT pg_size_pretty(pg_database_size('artifactor_v3'));"
```

### Redis Performance
```bash
# Memory usage
docker exec artifactor_backend_redis redis-cli INFO memory | grep used_memory_human

# Cache hit rate
docker exec artifactor_backend_redis redis-cli INFO stats | grep keyspace
```

### API Performance
```bash
# Response time test
curl -w "@-" -o /dev/null -s http://localhost:8000/api/health <<'EOF'
    time_namelookup:  %{time_namelookup}\n
       time_connect:  %{time_connect}\n
    time_appconnect:  %{time_appconnect}\n
   time_pretransfer:  %{time_pretransfer}\n
      time_redirect:  %{time_redirect}\n
 time_starttransfer:  %{time_starttransfer}\n
                    ----------\n
         time_total:  %{time_total}\n
EOF
```

## Backup and Restore

### Database Backup
```bash
# Create backup
docker exec artifactor_backend_postgres pg_dump -U artifactor artifactor_v3 > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
docker exec -i artifactor_backend_postgres psql -U artifactor artifactor_v3 < backup_20250101_120000.sql
```

### Redis Backup
```bash
# Trigger save
docker exec artifactor_backend_redis redis-cli BGSAVE

# Copy dump file
docker cp artifactor_backend_redis:/data/dump.rdb ./redis_backup_$(date +%Y%m%d_%H%M%S).rdb
```

### Volume Backup
```bash
# Backup all volumes
docker run --rm \
  -v artifactor_backend_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/postgres_backup_$(date +%Y%m%d_%H%M%S).tar.gz -C /data .

docker run --rm \
  -v artifactor_backend_redis_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/redis_backup_$(date +%Y%m%d_%H%M%S).tar.gz -C /data .

docker run --rm \
  -v artifactor_backend_upload_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/uploads_backup_$(date +%Y%m%d_%H%M%S).tar.gz -C /data .
```

## Troubleshooting

### Service Won't Start

**Check logs:**
```bash
docker-compose -f docker/backend-compose.yml logs backend
```

**Common issues:**
1. Port conflicts (8000, 5432, 6379 already in use)
2. Missing .env file
3. Invalid SECRET_KEY
4. Insufficient Docker resources

### Database Connection Issues

```bash
# Test direct connection
docker exec -it artifactor_backend_postgres psql -U artifactor -d artifactor_v3

# Check connection from backend
docker exec artifactor_backend_api python -c "import psycopg2; conn = psycopg2.connect('postgresql://artifactor:password@postgres:5432/artifactor_v3'); print('Connected!')"
```

### Redis Connection Issues

```bash
# Test Redis
docker exec artifactor_backend_redis redis-cli ping

# Check from backend
docker exec artifactor_backend_api python -c "import redis; r = redis.from_url('redis://redis:6379'); print(r.ping())"
```

### Backend API Not Responding

```bash
# Check if backend is running
docker ps | grep artifactor_backend_api

# Check health endpoint
curl -v http://localhost:8000/api/health

# Inspect backend logs
docker logs artifactor_backend_api --tail 100
```

### CORS Issues

If Chrome extension can't connect:

1. Verify CORS in backend logs
2. Check extension permissions in manifest.json
3. Ensure `chrome-extension://*` is in ALLOWED_ORIGINS

### Performance Issues

```bash
# Check resource limits
docker inspect artifactor_backend_api | grep -A 10 Memory

# Increase resources in backend-compose.yml:
deploy:
  resources:
    limits:
      memory: 2G  # Increase from 1G
      cpus: '2.0'  # Increase from 1.0
```

## Development Mode

For development with live reload:

1. Uncomment volume mounts in backend-compose.yml:
```yaml
volumes:
  - backend_upload_data:/app/uploads
  - ../backend/src:/app/src:ro  # Uncomment
  - ../backend/requirements.txt:/app/requirements.txt:ro  # Uncomment
```

2. Add `--reload` to command:
```yaml
command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

3. Restart services:
```bash
docker-compose -f docker/backend-compose.yml up -d --build
```

## Security Considerations

1. **Never commit .env file** to version control
2. **Use strong passwords** (32+ characters)
3. **Rotate SECRET_KEY** regularly
4. **Limit CORS origins** in production
5. **Enable TLS/SSL** for production deployments
6. **Regular security updates**: `docker-compose pull`

## Production Deployment

For production use:

1. Use `docker/docker-compose.secure.yml` instead
2. Enable TLS/SSL certificates
3. Configure firewall rules
4. Set up monitoring (Prometheus + Grafana)
5. Implement backup automation
6. Use secrets management (Docker Secrets, Vault)

## Additional Resources

- **Full Documentation**: `/home/john/ARTIFACTOR/docs/`
- **API Security Guide**: `/home/john/ARTIFACTOR/docs/API_SECURITY_GUIDE.md`
- **Production Deployment**: `/home/john/ARTIFACTOR/docs/PRODUCTION_DEPLOYMENT_GUIDE.md`
- **Troubleshooting**: `/home/john/ARTIFACTOR/docs/TROUBLESHOOTING_GUIDE.md`

## Support

- **Repository**: https://github.com/SWORDIntel/ARTIFACTOR
- **Issues**: GitHub Issues
- **Contact**: ARTIFACTOR@swordintelligence.airforce

---

**ARTIFACTOR v3.0** - Backend Services Configuration
Created: 2025-10-11
SWORD Intelligence - Advanced AI & Software Solutions
