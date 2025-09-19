# 🚀 ETHERSCAN API DEPLOYMENT INSTRUCTIONS

## Quick Deploy (30 seconds)

```bash
# Clone and deploy
cd /home/john
docker-compose up -d

# Verify deployment
docker ps
curl http://localhost:8080/health
```

**Login to Portainer**: https://localhost:9443
**Credentials**: RAVEN / 1/0523/6002608

---

## 📋 Complete Deployment Guide

### Prerequisites
- Docker 20.10+ installed
- Docker Compose 2.0+ installed
- 4GB+ RAM available
- 10GB+ disk space

### Step 1: Download and Prepare

```bash
# Navigate to deployment directory
cd /home/john

# Verify all files are present
ls -la
# Should see: docker-compose.yml, Dockerfile, etherscan_connector.py, api_server.py, etc.

# Check Docker is running
docker --version
docker-compose --version
```

### Step 2: Deploy the Stack

```bash
# Start all services
docker-compose up -d

# Monitor startup logs
docker-compose logs -f
```

### Step 3: Verify Deployment

```bash
# Check all containers are running
docker ps

# Test API health
curl http://localhost:8080/health

# Test Etherscan API functionality
curl "http://localhost:8080/api/balance/0x742d35Cc6634C0532925a3b8D91E5e45C56c9bE9"

# Test Redis cache
docker exec etherscan-redis redis-cli ping
```

### Step 4: Access Services

| Service | URL | Purpose |
|---------|-----|---------|
| **Portainer** | https://localhost:9443 | Container Management |
| **Etherscan API** | http://localhost:8080 | Main API Service |
| **Grafana** | http://localhost:3000 | Monitoring Dashboard |
| **Prometheus** | http://localhost:9090 | Metrics Collection |
| **Kibana** | http://localhost:5601 | Log Analysis |

**Portainer Login**: RAVEN / 1/0523/6002608

---

## 🎯 API Endpoints Available

### Balance Lookup
```bash
curl "http://localhost:8080/api/balance/0x742d35Cc6634C0532925a3b8D91E5e45C56c9bE9"
```

### Ethereum Price
```bash
curl "http://localhost:8080/api/price"
```

### Gas Oracle
```bash
curl "http://localhost:8080/api/gas"
```

### Transaction History
```bash
curl "http://localhost:8080/api/transactions/0x742d35Cc6634C0532925a3b8D91E5e45C56c9bE9"
```

### Health Check
```bash
curl "http://localhost:8080/health"
```

---

## 🐳 Container Management via Portainer

### Access Portainer
1. Open https://localhost:9443
2. Login: RAVEN / 1/0523/6002608
3. Navigate to "Containers"

### Common Operations

#### Restart API Service
1. Containers → etherscan-api → Restart

#### View Logs
1. Containers → etherscan-api → Logs

#### Clear Redis Cache
1. Containers → etherscan-redis → Console
2. Run: `FLUSHALL`

#### Scale Services
1. Stacks → etherscan-stack → Editor
2. Modify replicas and update

---

## 📊 Monitoring & Debugging

### Debug Dashboard
```bash
# Run comprehensive debug dashboard
python3 etherscan_debug_dashboard.py

# Run automated health check
./automated_recovery.sh check

# Start continuous monitoring
./automated_recovery.sh monitor 300
```

### Grafana Dashboards
1. Open http://localhost:3000
2. Login: admin / admin123
3. View pre-configured dashboards

### Prometheus Metrics
1. Open http://localhost:9090
2. Query metrics:
   - `http_requests_total`
   - `http_request_duration_seconds`
   - `cache_hits_total`

---

## 🔧 Configuration

### Environment Variables
Edit `docker-compose.yml` to modify:

```yaml
environment:
  - API_KEY=SHNQ2KS7N6D8B175GYUSJMESDKBZH7H8PS  # Your Etherscan API key
  - CACHE_TTL=300                                # Cache timeout in seconds
  - RATE_LIMIT=5                                 # Requests per second
```

### Resource Limits
Adjust memory/CPU limits in `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      memory: 512M    # Increase if needed
      cpus: '1.0'     # Adjust based on load
```

---

## 🚨 Troubleshooting

### Common Issues

#### API Not Responding
```bash
# Check container status
docker ps | grep etherscan-api

# Check logs
docker logs etherscan-api --tail 50

# Restart service
docker restart etherscan-api
```

#### Rate Limiting Issues
```bash
# Check current rate limit status
curl -I "https://api.etherscan.io/api?module=account&action=balance&address=0x742d35Cc6634C0532925a3b8D91E5e45C56c9bE9&tag=latest&apikey=SHNQ2KS7N6D8B175GYUSJMESDKBZH7H8PS"

# Increase cache TTL in api_server.py
# CACHE_TTL = 600  # 10 minutes
```

#### Redis Memory Issues
```bash
# Check Redis memory usage
docker exec etherscan-redis redis-cli info memory

# Clear cache if needed
docker exec etherscan-redis redis-cli FLUSHALL
```

#### High Resource Usage
```bash
# Check resource usage
docker stats --no-stream

# Scale down if needed
docker-compose scale etherscan-api=1
```

### Emergency Recovery
```bash
# Automated recovery
./automated_recovery.sh recover

# Full stack restart
docker-compose down && docker-compose up -d

# Clean Docker resources
docker system prune -f
```

---

## 🔒 Security Notes

### API Key Protection
- API key is stored in environment variables
- Never commit API keys to version control
- Rotate keys regularly

### Network Security
- Services communicate via internal Docker network
- Only necessary ports are exposed
- SSL/TLS enabled for Portainer

### Container Security
- Containers run as non-root users
- Read-only filesystems where possible
- Resource limits prevent DoS

---

## 📈 Performance Optimization

### Cache Configuration
- Redis cache with 256MB limit
- LRU eviction policy
- 5-minute default TTL

### Rate Limiting
- 5 requests/second to Etherscan API
- Exponential backoff on rate limits
- Request queuing and retry logic

### Resource Management
- Memory limits on all containers
- CPU limits to prevent resource hogging
- Health checks for auto-restart

---

## 🔄 Updates and Maintenance

### Daily Checks
```bash
./automated_recovery.sh check
docker logs etherscan-api --since 24h | grep -i error
```

### Weekly Maintenance
```bash
./automated_recovery.sh clean
docker-compose pull
```

### Monthly Updates
```bash
docker-compose down
docker system prune -f
docker-compose pull
docker-compose up -d
```

---

## 📞 Support

### Health Monitoring
- **Debug Dashboard**: `python3 etherscan_debug_dashboard.py`
- **Automated Recovery**: `./automated_recovery.sh`
- **Portainer Management**: https://localhost:9443

### Log Locations
- **API Logs**: `docker logs etherscan-api`
- **Redis Logs**: `docker logs etherscan-redis`
- **Nginx Logs**: `./nginx/logs/`
- **System Logs**: `/var/log/`

### Emergency Contacts
```yaml
API Issues: "./automated_recovery.sh recover"
Performance: "python3 etherscan_debug_dashboard.py"
Complete Outage: "docker-compose down && docker-compose up -d"
```

---

## ✅ Deployment Checklist

- [ ] Docker and Docker Compose installed
- [ ] All files present in deployment directory
- [ ] `docker-compose up -d` completed successfully
- [ ] All containers running (`docker ps`)
- [ ] API health check passes (`curl http://localhost:8080/health`)
- [ ] Portainer accessible (https://localhost:9443)
- [ ] Monitoring dashboards accessible
- [ ] Debug tools tested
- [ ] Backup procedures documented

**Deployment Status**: ✅ Production Ready
**API Key**: SHNQ2KS7N6D8B175GYUSJMESDKBZH7H8PS
**Portainer Access**: RAVEN / 1/0523/6002608

Your Etherscan API deployment is complete and ready for production use!