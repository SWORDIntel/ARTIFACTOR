# ARTIFACTOR v3.0.0 Troubleshooting Guide

**Comprehensive Troubleshooting & Maintenance Procedures**

*Complete problem diagnosis, resolution procedures, and preventive maintenance*

---

## 🔧 Executive Troubleshooting Overview

ARTIFACTOR v3.0.0 includes comprehensive troubleshooting tools and procedures for rapid problem diagnosis and resolution. This guide covers common issues, diagnostic procedures, and preventive maintenance.

### 🎯 Troubleshooting Status
- ✅ **Automated Diagnostics**: Comprehensive health checks and system validation
- ✅ **Performance Monitoring**: Real-time performance metrics and alerting
- ✅ **Security Monitoring**: Continuous security validation and incident response
- ✅ **Proactive Maintenance**: Scheduled maintenance and optimization
- ✅ **Recovery Procedures**: Tested disaster recovery and rollback procedures

---

## 🚨 Emergency Response Procedures

### Critical Issue Response (Severity 1)

#### Immediate Actions (0-5 minutes)
```bash
# 1. Assess system status
./scripts/emergency-status-check.sh

# Expected Output:
# 🚨 EMERGENCY STATUS CHECK
# ========================
# Backend Service: DOWN/UP
# Database Service: DOWN/UP
# Cache Service: DOWN/UP
# Frontend Service: DOWN/UP
# Overall Status: CRITICAL/WARNING/OK

# 2. Enable maintenance mode if needed
./scripts/enable-maintenance-mode.sh
echo "Maintenance mode activated - users see maintenance page"

# 3. Capture diagnostic information
./scripts/capture-emergency-logs.sh
# Creates: emergency_logs_$(date +%Y%m%d_%H%M%S).tar.gz
```

#### Emergency Service Recovery (5-15 minutes)
```bash
# 4. Restart failed services
docker-compose -f docker/docker-compose.yml restart

# 5. Verify service recovery
./scripts/verify-service-recovery.sh

# 6. Check for data integrity
./scripts/verify-data-integrity.sh

# 7. Disable maintenance mode
./scripts/disable-maintenance-mode.sh
echo "Services restored - maintenance mode disabled"
```

### High Priority Issue Response (Severity 2)

#### System Performance Issues
```bash
# Performance degradation response
./scripts/performance-emergency-check.sh

# Common performance fixes:
# 1. Clear cache if corrupted
curl -X DELETE http://localhost:8000/api/performance/cache/clear

# 2. Restart high-memory services
docker-compose restart backend redis

# 3. Database performance optimization
./scripts/emergency-db-optimization.sh

# 4. Check resource usage
docker stats --no-stream
df -h
free -h
```

---

## 🔍 Common Issues & Solutions

### 1. Service Startup Issues

#### Backend Service Won't Start
```bash
# Diagnostic steps
docker-compose logs backend | tail -50

# Common causes and solutions:

# A. Database connection issues
# Check database status
docker-compose exec postgres pg_isready -U artifactor
# If failed, restart database
docker-compose restart postgres

# B. Port conflicts
# Check port usage
sudo netstat -tlnp | grep :8000
# If port in use, stop conflicting service or change port

# C. Configuration errors
# Validate configuration
./scripts/validate-backend-config.sh
# Fix configuration errors in .env file

# D. Missing dependencies
# Rebuild backend image
docker-compose build --no-cache backend
docker-compose up -d backend
```

#### Frontend Service Won't Start
```bash
# Diagnostic steps
docker-compose logs frontend | tail -50

# Common causes and solutions:

# A. Node.js build issues
# Clear npm cache and rebuild
docker-compose exec frontend npm cache clean --force
docker-compose restart frontend

# B. Port conflicts
# Check port usage
sudo netstat -tlnp | grep :3000
# Change frontend port in docker-compose.yml if needed

# C. Environment issues
# Check environment variables
docker-compose exec frontend env | grep -E "(NODE_ENV|REACT_APP_)"
# Ensure proper environment configuration
```

#### Database Service Issues
```bash
# Diagnostic steps
docker-compose logs postgres | tail -50

# Common causes and solutions:

# A. Data directory permissions
# Fix permissions
docker-compose down
sudo chown -R 999:999 ./data/postgres
docker-compose up -d postgres

# B. Configuration issues
# Check PostgreSQL configuration
docker-compose exec postgres psql -U artifactor -c "SHOW all;"

# C. Disk space issues
# Check available space
df -h
# Clean up if needed
docker system prune -f
```

### 2. Performance Issues

#### High Response Times
```bash
# Diagnostic procedure
./scripts/diagnose-high-response-times.sh

# Step-by-step diagnosis:

# 1. Check system resources
top
iostat 1 5
free -h

# 2. Analyze API performance
curl http://localhost:8000/api/performance/metrics | jq '.response_times'

# 3. Check database performance
curl http://localhost:8000/api/performance/database/slow_queries

# 4. Analyze cache performance
curl http://localhost:8000/api/performance/cache/stats

# Solutions:
# A. Database optimization
./scripts/optimize-database-performance.sh

# B. Cache warming
curl -X POST http://localhost:8000/api/performance/cache/warm

# C. Restart services
docker-compose restart backend redis

# D. Scale services if needed
docker-compose -f docker/docker-compose.scale.yml up -d --scale backend=3
```

#### Memory Issues
```bash
# Memory usage analysis
./scripts/analyze-memory-usage.sh

# Check container memory usage
docker stats --no-stream --format "table {{.Container}}\t{{.MemUsage}}\t{{.MemPerc}}"

# Solutions:
# A. Restart memory-intensive services
docker-compose restart backend frontend

# B. Clear caches
curl -X DELETE http://localhost:8000/api/performance/cache/clear
docker-compose exec redis redis-cli FLUSHALL

# C. Optimize garbage collection
curl -X POST http://localhost:8000/api/performance/gc/optimize

# D. Check for memory leaks
./scripts/check-memory-leaks.sh
```

### 3. Database Issues

#### Connection Pool Exhaustion
```bash
# Diagnostic steps
curl http://localhost:8000/api/performance/database/connections

# Expected healthy response:
# {
#   "active_connections": 15,
#   "max_connections": 20,
#   "pool_usage": "75%",
#   "status": "healthy"
# }

# If pool exhausted:
# {
#   "active_connections": 20,
#   "max_connections": 20,
#   "pool_usage": "100%",
#   "status": "exhausted"
# }

# Solutions:
# A. Restart backend to clear connections
docker-compose restart backend

# B. Check for long-running queries
docker-compose exec postgres psql -U artifactor -d artifactor_v3 -c "
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';"

# C. Increase pool size (temporary)
# Edit .env file:
# DATABASE_POOL_SIZE=30
# DATABASE_MAX_OVERFLOW=40
# Then restart: docker-compose restart backend
```

#### Slow Database Queries
```bash
# Identify slow queries
curl http://localhost:8000/api/performance/database/slow_queries

# Database query analysis
docker-compose exec postgres psql -U artifactor -d artifactor_v3 -c "
SELECT query, mean_time, calls, rows
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;"

# Solutions:
# A. Optimize indexes
./scripts/optimize-database-indexes.sh

# B. Analyze and update table statistics
docker-compose exec postgres psql -U artifactor -d artifactor_v3 -c "ANALYZE;"

# C. Vacuum and reindex
docker-compose exec postgres psql -U artifactor -d artifactor_v3 -c "VACUUM ANALYZE;"
```

#### Database Lock Issues
```bash
# Check for locks
docker-compose exec postgres psql -U artifactor -d artifactor_v3 -c "
SELECT blocked_locks.pid AS blocked_pid,
       blocked_activity.usename AS blocked_user,
       blocking_locks.pid AS blocking_pid,
       blocking_activity.usename AS blocking_user,
       blocked_activity.query AS blocked_statement,
       blocking_activity.query AS current_statement_in_blocking_process
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
    AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
    AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
    AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
    AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
    AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
    AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
    AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
    AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
    AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
    AND blocking_locks.pid != blocked_locks.pid
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;"

# Solutions:
# A. Terminate blocking queries (if safe)
# docker-compose exec postgres psql -U artifactor -d artifactor_v3 -c "SELECT pg_terminate_backend(PID);"

# B. Restart database (last resort)
# docker-compose restart postgres
```

### 4. Cache Issues

#### Redis Connection Issues
```bash
# Check Redis status
docker-compose exec redis redis-cli ping
# Expected: PONG

# If Redis is down:
docker-compose logs redis | tail -20
docker-compose restart redis

# Test Redis functionality
docker-compose exec redis redis-cli
> SET test "value"
> GET test
> EXIT

# Check Redis memory usage
docker-compose exec redis redis-cli INFO memory
```

#### Cache Performance Issues
```bash
# Analyze cache performance
curl http://localhost:8000/api/performance/cache/analysis

# Check cache hit rates
curl http://localhost:8000/api/performance/cache/stats | jq '.hit_rate'

# If hit rate is low (<70%):
# A. Warm cache with frequently accessed data
curl -X POST http://localhost:8000/api/performance/cache/warm

# B. Optimize cache configuration
curl -X POST http://localhost:8000/api/performance/cache/optimize

# C. Check cache size and eviction policy
docker-compose exec redis redis-cli INFO stats
```

### 5. Authentication & Authorization Issues

#### JWT Token Issues
```bash
# Test token validation
curl -X GET http://localhost:8000/api/auth/validate \
  -H "Authorization: Bearer YOUR_TOKEN"

# Common token issues:

# A. Expired tokens
# Solution: Refresh token
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Authorization: Bearer YOUR_REFRESH_TOKEN"

# B. Invalid token signature
# Check JWT secret configuration in .env
# Restart backend if secret was changed
docker-compose restart backend

# C. Token blacklisting issues
# Check Redis for blacklisted tokens
docker-compose exec redis redis-cli KEYS "blacklist:*"
```

#### Permission Issues
```bash
# Test user permissions
curl -X GET http://localhost:8000/api/users/me \
  -H "Authorization: Bearer YOUR_TOKEN"

# Check user role and permissions
curl -X GET http://localhost:8000/api/auth/permissions \
  -H "Authorization: Bearer YOUR_TOKEN"

# Solutions:
# A. Update user role (admin only)
curl -X PUT http://localhost:8000/api/users/USER_ID \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"role": "user"}'

# B. Clear user cache if permissions cached
curl -X DELETE http://localhost:8000/api/cache/user/USER_ID \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

### 6. File Upload Issues

#### Upload Failures
```bash
# Check upload directory permissions
ls -la uploads/
# Should show write permissions for the application

# Check disk space
df -h
# Ensure sufficient space in upload directory

# Test upload endpoint
curl -X POST http://localhost:8000/api/artifacts/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test.txt"

# Solutions:
# A. Fix permissions
sudo chown -R 1000:1000 uploads/
sudo chmod -R 755 uploads/

# B. Clean up old uploads
./scripts/cleanup-old-uploads.sh

# C. Check file size limits
# Edit .env: MAX_FILE_SIZE=104857600 (100MB)
```

---

## 📊 Diagnostic Tools & Scripts

### System Health Check
```bash
# Comprehensive system health check
./scripts/system-health-check.sh

# Expected Output:
# 🏥 ARTIFACTOR System Health Check
# =================================
# ✅ Backend Service: Healthy (Response: 120ms)
# ✅ Frontend Service: Healthy
# ✅ Database Service: Healthy (Connections: 5/20)
# ✅ Cache Service: Healthy (Memory: 45MB/256MB)
# ✅ Disk Space: 65GB available (Good)
# ✅ Memory Usage: 6.2GB/16GB (Good)
# ✅ CPU Usage: 25% (Good)
# ⚠️ SSL Certificate: Expires in 30 days
# 🎉 Overall Health: Good
```

### Performance Diagnostics
```bash
# Performance diagnostic suite
./scripts/performance-diagnostics.sh

# Includes:
# - API response time analysis
# - Database query performance
# - Cache hit rate analysis
# - Memory usage patterns
# - CPU utilization trends
# - Disk I/O analysis
```

### Security Diagnostics
```bash
# Security diagnostic check
./scripts/security-diagnostics.sh

# Includes:
# - Authentication system status
# - Failed login attempt analysis
# - Permission violation detection
# - Security configuration validation
# - Audit log analysis
# - Security alert review
```

### Network Diagnostics
```bash
# Network connectivity diagnostics
./scripts/network-diagnostics.sh

# Tests:
# - Internal service connectivity
# - Database connection health
# - Cache connection health
# - External API connectivity
# - DNS resolution
# - SSL certificate validation
```

---

## 🔧 Maintenance Procedures

### Daily Maintenance Tasks

#### Automated Daily Maintenance
```bash
# Daily maintenance script
./scripts/daily-maintenance.sh

# Tasks performed:
# 1. System health check
# 2. Log rotation and cleanup
# 3. Backup verification
# 4. Performance monitoring
# 5. Security log review
# 6. Database maintenance
# 7. Cache optimization
# 8. Resource usage analysis

# Expected Output:
# 📅 Daily Maintenance Report - $(date)
# =====================================
# ✅ System Health: All services healthy
# ✅ Log Rotation: Completed successfully
# ✅ Backup Status: Last backup successful
# ✅ Performance: All metrics within targets
# ✅ Security: No security alerts
# ✅ Database: Maintenance completed
# ✅ Cache: Performance optimized
# ✅ Resources: Usage within limits
# 📋 Daily maintenance completed successfully
```

#### Manual Daily Checks
```bash
# Check system status
./scripts/quick-status-check.sh

# Review overnight logs
./scripts/review-overnight-logs.sh

# Check backup status
./scripts/check-backup-status.sh

# Monitor performance metrics
curl http://localhost:8000/api/performance/dashboard
```

### Weekly Maintenance Tasks

#### Automated Weekly Maintenance
```bash
# Weekly maintenance script
./scripts/weekly-maintenance.sh

# Tasks performed:
# 1. Comprehensive system analysis
# 2. Performance optimization
# 3. Security updates check
# 4. Database optimization
# 5. Cache performance tuning
# 6. Log analysis and archival
# 7. Capacity planning review
# 8. Documentation updates
```

#### Performance Optimization
```bash
# Weekly performance optimization
./scripts/weekly-performance-optimization.sh

# Includes:
# - Database index optimization
# - Cache configuration tuning
# - Query performance analysis
# - Resource usage optimization
# - Performance baseline updates
```

### Monthly Maintenance Tasks

#### Comprehensive Monthly Review
```bash
# Monthly maintenance suite
./scripts/monthly-maintenance.sh

# Major tasks:
# 1. Full security audit
# 2. Performance trend analysis
# 3. Capacity planning update
# 4. Disaster recovery testing
# 5. Security policy review
# 6. Documentation updates
# 7. Compliance verification
# 8. Backup strategy review
```

#### Security Maintenance
```bash
# Monthly security maintenance
./scripts/monthly-security-maintenance.sh

# Tasks:
# - Security patch updates
# - Credential rotation
# - Access review
# - Security configuration audit
# - Penetration testing
# - Compliance reporting
```

---

## 🚨 Disaster Recovery Procedures

### Data Recovery

#### Database Recovery
```bash
# Database recovery from backup
./scripts/recover-database.sh --backup-date YYYY-MM-DD

# Steps:
# 1. Stop application services
# 2. Backup current database
# 3. Restore from backup
# 4. Verify data integrity
# 5. Restart services
# 6. Validate functionality

# Manual database recovery
docker-compose down
docker volume rm artifactor_postgres_data
docker-compose up -d postgres
sleep 30
gunzip -c backups/db_backup_YYYYMMDD.sql.gz | \
  docker-compose exec -T postgres psql -U artifactor -d artifactor_v3
```

#### Application Data Recovery
```bash
# Application data recovery
./scripts/recover-application-data.sh --backup-date YYYY-MM-DD

# Recovers:
# - User uploaded files
# - Configuration files
# - SSL certificates
# - Plugin data
# - Log archives
```

### Service Recovery

#### Complete System Recovery
```bash
# Full system disaster recovery
./scripts/disaster-recovery.sh --backup-location /path/to/backups

# Recovery process:
# 1. System assessment and preparation
# 2. Infrastructure restoration
# 3. Database recovery
# 4. Application data restoration
# 5. Service deployment
# 6. Configuration restoration
# 7. Security validation
# 8. Performance verification
# 9. User notification
```

#### Rollback Procedures
```bash
# Emergency rollback to previous version
./scripts/emergency-rollback.sh --to-version v3.0.0

# Rollback process:
# 1. Stop current services
# 2. Backup current state
# 3. Restore previous container images
# 4. Restore previous database state
# 5. Update configuration
# 6. Restart services
# 7. Verify rollback success
# 8. Monitor for issues
```

---

## 📋 Preventive Maintenance

### Proactive Monitoring

#### Performance Monitoring
```bash
# Set up continuous performance monitoring
./scripts/setup-performance-monitoring.sh

# Monitors:
# - API response times
# - Database query performance
# - Cache hit rates
# - Memory usage patterns
# - CPU utilization
# - Disk I/O metrics
```

#### Security Monitoring
```bash
# Set up security monitoring
./scripts/setup-security-monitoring.sh

# Monitors:
# - Failed authentication attempts
# - Permission violations
# - Unusual access patterns
# - Security configuration changes
# - System intrusion attempts
# - Compliance violations
```

#### Resource Monitoring
```bash
# Set up resource monitoring
./scripts/setup-resource-monitoring.sh

# Monitors:
# - Disk space usage
# - Memory consumption
# - CPU utilization
# - Network usage
# - Container health
# - Service availability
```

### Capacity Planning

#### Capacity Analysis
```bash
# Generate capacity planning report
./scripts/generate-capacity-report.sh

# Analysis includes:
# - Current resource utilization
# - Usage trend analysis
# - Growth projections
# - Scaling recommendations
# - Cost optimization suggestions
```

#### Resource Optimization
```bash
# Optimize resource allocation
./scripts/optimize-resource-allocation.sh

# Optimizations:
# - Container resource limits
# - Database connection pools
# - Cache memory allocation
# - Worker process tuning
# - Network configuration
```

---

## 📞 Support & Escalation

### Support Tiers

#### Level 1 Support (Application Issues)
- **Response Time**: 4 hours during business hours
- **Coverage**: Application functionality, user issues, basic configuration
- **Contact**: ARTIFACTOR@swordintelligence.airforce

#### Level 2 Support (System Issues)
- **Response Time**: 2 hours during business hours, 4 hours after hours
- **Coverage**: Performance issues, integration problems, advanced configuration
- **Contact**: support@swordintelligence.airforce

#### Level 3 Support (Critical Issues)
- **Response Time**: 1 hour 24/7
- **Coverage**: System outages, security incidents, data loss
- **Contact**: emergency@swordintelligence.airforce

### Escalation Procedures

#### Critical Issue Escalation
```bash
# For critical issues affecting system availability
# 1. Immediate notification
./scripts/notify-critical-issue.sh --severity critical --description "System outage"

# 2. Gather diagnostic information
./scripts/gather-emergency-diagnostics.sh

# 3. Implement immediate workarounds
./scripts/apply-emergency-workarounds.sh

# 4. Escalate to Level 3 support
# Contact: emergency@swordintelligence.airforce
# Include: diagnostic files, impact assessment, business impact
```

---

## 🎯 Troubleshooting Quick Reference

### Quick Diagnostic Commands
```bash
# System health
./scripts/quick-health-check.sh

# Service status
docker-compose ps

# Resource usage
docker stats --no-stream

# Application logs
docker-compose logs --tail=50 backend frontend

# Database status
docker-compose exec postgres pg_isready -U artifactor

# Cache status
docker-compose exec redis redis-cli ping

# API health
curl -f http://localhost:8000/api/health

# Performance metrics
curl http://localhost:8000/api/metrics
```

### Common Issue Quick Fixes
```bash
# Service restart
docker-compose restart <service-name>

# Clear cache
curl -X DELETE http://localhost:8000/api/cache/clear

# Database connection reset
docker-compose restart backend

# Memory cleanup
docker system prune -f

# Log cleanup
./scripts/cleanup-logs.sh

# Emergency maintenance mode
./scripts/enable-maintenance-mode.sh
```

---

## 🎯 Conclusion

ARTIFACTOR v3.0.0 Troubleshooting Guide provides:

### 🔧 Diagnostic Excellence
- ✅ **Comprehensive Health Checks** with automated diagnostics
- ✅ **Performance Monitoring** with real-time metrics and alerting
- ✅ **Security Monitoring** with continuous validation and incident response
- ✅ **Proactive Maintenance** with scheduled optimization and monitoring
- ✅ **Emergency Procedures** with rapid response and recovery

### 🛠️ Operational Excellence
- ✅ **Quick Resolution** with step-by-step troubleshooting procedures
- ✅ **Preventive Maintenance** with proactive monitoring and optimization
- ✅ **Disaster Recovery** with tested backup and recovery procedures
- ✅ **Support Structure** with tiered support and escalation procedures
- ✅ **Documentation** with comprehensive operational runbooks

ARTIFACTOR v3.0.0 ensures maximum uptime and performance through comprehensive troubleshooting and maintenance procedures.

---

**Troubleshooting Status**: 🔧 **COMPREHENSIVE**
**Diagnostic Coverage**: ✅ **COMPLETE**
**Recovery Procedures**: 🔄 **TESTED**
**Support Structure**: 📞 **24/7 AVAILABLE**

*ARTIFACTOR v3.0.0 Troubleshooting Guide - Complete Operational Support*
*Generated: 2025-09-23*
*Contact: ARTIFACTOR@swordintelligence.airforce*