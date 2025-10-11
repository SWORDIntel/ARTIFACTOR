# ARTIFACTOR Backend - Quick Start Guide

**Get your Chrome Extension backend running in 3 simple steps**

---

## Prerequisites Check

Before starting, ensure you have:

- ✅ **Docker installed** (version 20.10 or higher)
- ✅ **Docker daemon running** (`sudo systemctl start docker`)
- ✅ **2GB free disk space**
- ✅ **Ports available**: 5432 (PostgreSQL), 6379 (Redis), 8000 (API)

### Quick Check Command
```bash
# Verify Docker is ready
docker --version && docker ps >/dev/null 2>&1 && echo "✓ Docker ready" || echo "✗ Docker not ready"
```

---

## 3-Step Installation

### Step 1: Start Backend Services

**Automatic 1-Click Start:**
```bash
./start-backend start
```

This single command will:
- ✓ Check all system requirements
- ✓ Generate secure credentials automatically
- ✓ Start PostgreSQL database
- ✓ Start Redis cache server
- ✓ Start FastAPI backend
- ✓ Run health checks on all services
- ✓ Display connection endpoints

**Expected Output:**
```
════════════════════════════════════════════════════════════
  Backend Ready
════════════════════════════════════════════════════════════

✓ All services are healthy and running!

Service Endpoints:
  🗄 PostgreSQL:  localhost:5432
  ⚡ Redis:       localhost:6379
  📡 Backend API: http://localhost:8000

API Documentation:
  Swagger UI:  http://localhost:8000/docs
  ReDoc:       http://localhost:8000/redoc
  Health:      http://localhost:8000/api/health

Chrome Extension Configuration:
  API URL:     http://localhost:8000/api
  WebSocket:   ws://localhost:8000/ws
```

**Time to complete:** ~60 seconds (first run), ~15 seconds (subsequent runs)

---

### Step 2: Verify Installation

**Check Service Health:**
```bash
./start-backend status
```

**Expected Output:**
```
Container Status:
  ✓ PostgreSQL - Running (Healthy)
  ✓ Redis - Running (Healthy)
  ✓ Backend API - Running (Healthy)

Port Status:
  ✓ Port 5432 (PostgreSQL): In Use
  ✓ Port 6379 (Redis): In Use
  ✓ Port 8000 (Backend API): In Use
```

**Test API Endpoint:**
```bash
curl http://localhost:8000/api/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "agent_bridge": {"status": "active"},
  "version": "3.0.0"
}
```

---

### Step 3: Configure Chrome Extension

#### Option A: Using Extension Options
1. **Open Chrome** and navigate to `chrome://extensions/`
2. **Find ARTIFACTOR extension** and click "Options"
3. **Enter Backend URL**: `http://localhost:8000`
4. **Click "Test Connection"** - should show green checkmark
5. **Save settings**

#### Option B: Manual Configuration
The extension auto-detects `localhost:8000` if running. No configuration needed for local development!

---

## First-Time Verification

### Test Artifact Upload
```bash
# Create a test file
echo "console.log('Hello from ARTIFACTOR');" > test.js

# Upload via API
curl -X POST http://localhost:8000/api/artifacts/upload \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test.js"
```

### Browse API Documentation
Open in your browser:
- **Interactive API Docs**: http://localhost:8000/docs
- **Full Documentation**: http://localhost:8000/redoc

---

## Daily Usage Commands

```bash
# Start backend services
./start-backend start

# Check service health
./start-backend status

# View live logs
./start-backend follow

# Stop all services
./start-backend stop

# Restart services
./start-backend restart
```

---

## Chrome Extension Connection Test

### Test from Extension Popup
1. **Visit Claude.ai** and open a conversation
2. **Click ARTIFACTOR extension** icon
3. **Check status indicator** - should show "Connected"
4. **Artifact count** will display if any artifacts detected

### Test from Extension Options
1. **Right-click extension** icon → "Options"
2. **Scroll to "Backend Connection"** section
3. **Click "Test Connection"** button
4. **Verify green checkmark** and response time display

---

## Troubleshooting Quick Tips

### ❌ Port Already In Use
```bash
# Find and stop conflicting services
sudo systemctl stop postgresql redis

# Or use ARTIFACTOR's built-in commands
./start-backend stop
./start-backend start
```

### ❌ Docker Permission Denied
```bash
# Add your user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Or run with sudo (not recommended)
sudo ./start-backend start
```

### ❌ Services Not Healthy
```bash
# Check detailed logs
./start-backend logs

# Reset everything and start fresh
./start-backend reset  # WARNING: Deletes all data
./start-backend start
```

### ❌ Connection Refused from Extension
1. **Verify services are running**: `./start-backend status`
2. **Check firewall settings**: `sudo ufw allow 8000`
3. **Test with curl**: `curl http://localhost:8000/api/health`
4. **Check extension URL**: Must be `http://localhost:8000` (no trailing slash)

### ❌ Slow Performance
```bash
# Check resource usage
./start-backend status

# View real-time metrics
docker stats artifactor_postgres artifactor_redis artifactor_backend
```

---

## What Gets Installed?

### Services Running
- **PostgreSQL 15** - Production database (Alpine Linux)
- **Redis 7** - High-performance cache server
- **FastAPI Backend** - REST API with WebSocket support

### Automatic Configuration
- ✓ **Secure credentials** generated automatically
- ✓ **Database schema** created on first run
- ✓ **Health checks** configured for all services
- ✓ **Resource limits** set for optimal performance
- ✓ **Logging** configured for troubleshooting

### Data Storage
- **Database**: `docker volume artifactor_postgres_data`
- **Cache**: `docker volume artifactor_redis_data`
- **Uploads**: `docker volume artifactor_upload_data`

To backup your data:
```bash
docker run --rm -v artifactor_postgres_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/backup.tar.gz -C /data .
```

---

## Performance Expectations

### First Run (Cold Start)
- Installation time: ~60 seconds
- Container downloads: ~100MB total
- Disk usage: ~500MB with data

### Normal Operation
- Startup time: ~15 seconds
- API response time: <150ms average
- Memory usage: ~300MB total (all services)
- Concurrent users: 100+ supported

### Recommended Resources
- **Development**: 2GB RAM, 2 CPU cores
- **Production**: 4GB RAM, 4 CPU cores
- **Storage**: 5GB minimum, SSD recommended

---

## Next Steps

### Explore API Features
```bash
# View all available endpoints
curl http://localhost:8000/api/docs

# Browse interactive documentation
open http://localhost:8000/docs  # macOS
xdg-open http://localhost:8000/docs  # Linux
```

### Enable Advanced Features
- **ML Classification**: Automatic artifact categorization
- **Semantic Search**: Advanced search capabilities
- **Real-time Collaboration**: Multi-user features
- **Plugin System**: Extend functionality

See [BACKEND_CONNECTION.md](chrome-extension/BACKEND_CONNECTION.md) for detailed configuration.

### Production Deployment
For production use with HTTPS, monitoring, and load balancing:
```bash
# Use secure production configuration
docker-compose -f docker/docker-compose.secure.yml up -d

# View production deployment guide
cat docs/PRODUCTION_DEPLOYMENT_GUIDE.md
```

---

## Common Use Cases

### Chrome Extension + Local Backend
**Perfect for**: Development, testing, offline usage
```bash
./start-backend start  # Start once, use all day
```

### Multiple Devices
**Perfect for**: Team collaboration, shared artifact library
1. Configure backend on one machine
2. Use `http://backend-ip:8000` in other extensions
3. All devices share same artifact database

### Continuous Integration
**Perfect for**: Automated testing, deployment pipelines
```bash
# CI/CD script
./start-backend start
./start-backend status || exit 1
pytest tests/
./start-backend stop
```

---

## Getting Help

### Quick Diagnostics
```bash
# Full system check
./start-backend status

# View error logs
./start-backend logs

# Check Docker daemon
sudo systemctl status docker
```

### Documentation
- **Backend Connection**: `chrome-extension/BACKEND_CONNECTION.md`
- **API Reference**: http://localhost:8000/docs (when running)
- **Troubleshooting**: `docs/TROUBLESHOOTING_GUIDE.md`
- **Production Setup**: `docs/PRODUCTION_DEPLOYMENT_GUIDE.md`

### Support Channels
- **GitHub Issues**: https://github.com/SWORDIntel/ARTIFACTOR/issues
- **Email**: ARTIFACTOR@swordintelligence.airforce
- **Documentation**: https://github.com/SWORDIntel/ARTIFACTOR

---

## Success Checklist

After completing this quick start, you should have:

- ✅ Backend services running and healthy
- ✅ API responding at http://localhost:8000
- ✅ Database and cache operational
- ✅ Chrome extension connected successfully
- ✅ Able to view API documentation
- ✅ Basic artifact operations working

**Congratulations! Your ARTIFACTOR backend is ready to use.**

---

**ARTIFACTOR v3.0.0** - Enterprise-Grade Artifact Management
*Making Claude.ai artifact management professional and efficient*

**Repository**: https://github.com/SWORDIntel/ARTIFACTOR
**Contact**: ARTIFACTOR@swordintelligence.airforce
