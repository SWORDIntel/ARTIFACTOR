# 🔗 ETHERSCAN API Docker Stack

Production-ready Etherscan API deployment with comprehensive monitoring, debugging, and container management.

## 🚀 Quick Start

```bash
# Deploy stack
docker-compose up -d

# Access services
# Portainer: https://localhost:9443 (RAVEN / 1/0523/6002608)
# API: http://localhost:8080
# Grafana: http://localhost:3000
```

## 📊 Services Included

| Service | Port | Purpose |
|---------|------|---------|
| **Etherscan API** | 8080 | Main API service with caching |
| **Portainer** | 9443 | Container management UI |
| **Redis** | 6379 | Cache and rate limiting |
| **Nginx** | 80/443 | Reverse proxy with SSL |
| **Prometheus** | 9090 | Metrics collection |
| **Grafana** | 3000 | Monitoring dashboards |
| **Kibana** | 5601 | Log analysis |

## 🎯 API Endpoints

- GET /api/balance/{address} - Get ETH balance
- GET /api/price - Get current ETH price
- GET /api/gas - Get gas oracle data
- GET /api/transactions/{address} - Get transaction history
- GET /health - Health check

## 🔧 Features

- Production Ready - SSL, monitoring, logging
- Auto-scaling - Docker Swarm compatible
- Monitoring - Prometheus + Grafana dashboards
- Caching - Redis with intelligent TTL
- Rate Limiting - Etherscan API protection
- Security - SSL/TLS, container isolation
- Debugging - Comprehensive debug tools
- Recovery - Automated failure recovery

## 📋 Documentation

- DEPLOYMENT_INSTRUCTIONS.md - Complete deployment guide
- DEBUGGER_TACTICAL_ANALYSIS.md - Debugging procedures
- ETHERSCAN_DEBUG_FINAL.md - Debug tools and monitoring

## 🔒 Configuration

API Key: Configured via environment variables
Portainer: RAVEN user with secure password
SSL: Self-signed certificates included

## 🚨 Support

- Debug Dashboard: python3 etherscan_debug_dashboard.py
- Automated Recovery: ./automated_recovery.sh check
- Health Monitoring: Continuous via Portainer

Built with enterprise-grade reliability and monitoring.