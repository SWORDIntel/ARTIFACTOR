# 🔧 ETHERSCAN API COMPREHENSIVE DEBUG GUIDE

## Quick Start Debug Commands

```bash
# Run the comprehensive debug dashboard
python3 etherscan_debug_dashboard.py

# Run automated health check
./automated_recovery.sh check

# Get detailed system status
./automated_recovery.sh status

# Start continuous monitoring (every 5 minutes)
./automated_recovery.sh monitor 300

# Emergency recovery
./automated_recovery.sh recover
```

## 🚨 Emergency Response Procedures

### 1. Complete System Down
```bash
# Check if Docker is running
sudo systemctl status docker

# If Docker is down, start it
sudo systemctl start docker

# Restart entire stack
docker-compose down && docker-compose up -d

# Wait and check
sleep 30
./automated_recovery.sh check
```

### 2. API Not Responding
```bash
# Check API container logs
docker logs etherscan-api --tail 50

# Test direct API connection
curl -v http://localhost:8080/health

# Restart API container
docker restart etherscan-api
```

### 3. Redis Cache Issues
```bash
# Check Redis connectivity
docker exec etherscan-redis redis-cli ping

# Check Redis memory usage
docker exec etherscan-redis redis-cli info memory

# Clear cache if corrupted
docker exec etherscan-redis redis-cli FLUSHALL

# Restart Redis
docker restart etherscan-redis
```

## 🔍 Detailed Debugging Tools

### Debug Dashboard Features
The `etherscan_debug_dashboard.py` provides:

1. **Real-time Container Monitoring**
   - Docker container status
   - Health check results
   - Resource utilization

2. **API Performance Testing**
   - Response time measurement
   - Rate limiting verification
   - Error handling validation

3. **Cache Performance Analysis**
   - Redis connectivity
   - Cache hit rate monitoring
   - Performance speedup metrics

4. **System Resource Monitoring**
   - CPU, memory, disk usage
   - Alert thresholds
   - Performance bottleneck detection

5. **Automated Diagnostics**
   - Etherscan API connectivity
   - Rate limiting behavior
   - Caching effectiveness
   - Error handling validation

## 📊 Performance Metrics & Thresholds

### Normal Operating Parameters
```yaml
api_response_time: < 2.0 seconds
cache_hit_rate: > 80%
cpu_usage: < 70%
memory_usage: < 80%
disk_usage: < 85%
redis_keys: 100-10000 (depending on usage)
docker_containers: 8+ running
```

### Alert Thresholds
```yaml
critical:
  api_response_time: > 10.0 seconds
  cpu_usage: > 95%
  memory_usage: > 95%
  disk_usage: > 95%

warning:
  api_response_time: > 5.0 seconds
  cache_hit_rate: < 50%
  cpu_usage: > 80%
  memory_usage: > 85%
  disk_usage: > 90%
```

## 🔧 Common Issues & Solutions

### Issue: API Key Rate Limiting
**Symptoms:**
- HTTP 429 responses
- "Max rate limit reached" errors
- Slow response times

**Solutions:**
```bash
# Check current rate limit status
curl -I "https://api.etherscan.io/api?module=account&action=balance&address=0x742d35Cc6634C0532925a3b8D91E5e45C56c9bE9&tag=latest&apikey=SHNQ2KS7N6D8B175GYUSJMESDKBZH7H8PS"

# Verify cache is working to reduce API calls
docker exec etherscan-redis redis-cli info stats

# Increase cache TTL if needed (edit api_server.py)
# CACHE_TTL = 300  # 5 minutes instead of 30 seconds
```

### Issue: Redis Memory Full
**Symptoms:**
- Cache operations failing
- "OOM command not allowed" errors
- High memory usage

**Solutions:**
```bash
# Check Redis memory usage
docker exec etherscan-redis redis-cli info memory

# Clear cache if necessary
docker exec etherscan-redis redis-cli FLUSHALL

# Monitor memory usage
watch "docker exec etherscan-redis redis-cli info memory | grep used_memory_human"
```

### Issue: Container Crashes
**Symptoms:**
- Containers repeatedly restarting
- "Exit code" errors in logs
- Services unavailable

**Solutions:**
```bash
# Check container logs
docker logs etherscan-api --tail 100

# Check system resources
docker stats --no-stream

# Check for port conflicts
netstat -tulpn | grep :8080
```

## 📋 Maintenance Procedures

### Daily Maintenance
```bash
# Run health check
./automated_recovery.sh check

# Review logs for errors
docker logs etherscan-api --since 24h | grep -i error

# Check disk space
df -h

# Monitor performance
python3 etherscan_debug_dashboard.py
```

### Weekly Maintenance
```bash
# Clean Docker resources
./automated_recovery.sh clean

# Update container images
docker-compose pull

# Backup configuration
tar -czf backup-$(date +%Y%m%d).tar.gz docker-compose.yml nginx/ prometheus/

# Review and rotate logs
find /var/log -name "*.log" -mtime +7 -delete
```

## 🎯 Quick Reference Commands

```bash
# Essential debugging commands
docker ps                                    # Check container status
docker logs etherscan-api --tail 50        # Check API logs
docker stats --no-stream                   # Resource usage
./automated_recovery.sh check              # Health check
python3 etherscan_debug_dashboard.py       # Full dashboard
curl http://localhost:8080/health          # API health
docker exec etherscan-redis redis-cli ping # Redis check

# Emergency recovery
./automated_recovery.sh recover            # Automated recovery
docker-compose restart                     # Restart all services
docker-compose down && docker-compose up -d # Full restart

# Performance monitoring
./automated_recovery.sh monitor 300        # Continuous monitoring
./automated_recovery.sh status             # Detailed status report
```

## 📞 Emergency Contacts

```yaml
service_issues:
  command: "./automated_recovery.sh recover"

performance_degradation:
  command: "python3 etherscan_debug_dashboard.py"

complete_outage:
  command: "docker-compose down && docker-compose up -d"
```

This comprehensive debug guide provides everything needed to monitor, troubleshoot, and maintain the Etherscan API deployment in production.