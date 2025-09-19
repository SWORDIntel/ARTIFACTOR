#!/usr/bin/env python3
"""
Production Etherscan API Server with Claude.ai Integration
DOCKER-AGENT Implementation with Comprehensive Monitoring
"""

from flask import Flask, jsonify, request, g
from flask_cors import CORS
from etherscan_connector import EtherscanConnector
import logging
import time
import threading
import os
import json
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize Etherscan connector
connector = EtherscanConnector()

# Prometheus metrics
REQUEST_COUNT = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('api_request_duration_seconds', 'Request latency')
ACTIVE_CONNECTIONS = Gauge('api_active_connections', 'Active connections')
ETHERSCAN_CALLS = Counter('etherscan_api_calls_total', 'Total Etherscan API calls', ['endpoint'])
CACHE_HITS = Counter('cache_hits_total', 'Cache hits', ['endpoint'])
ERROR_COUNT = Counter('api_errors_total', 'API errors', ['type'])

# Health monitoring variables
health_metrics = {
    'start_time': time.time(),
    'total_requests': 0,
    'successful_requests': 0,
    'failed_requests': 0,
    'avg_response_time': 0,
    'last_api_check': None,
    'api_status': 'unknown',
    'cache_size': 0
}

# Request cache for performance optimization
request_cache = {}
cache_ttl = {
    'balance': 30,      # 30 seconds for balance
    'price': 60,        # 1 minute for price
    'gas': 30,          # 30 seconds for gas
    'transactions': 300  # 5 minutes for transactions
}

# Rate limiting (simple in-memory)
rate_limits = {}
RATE_LIMIT_REQUESTS = 60  # requests per minute per IP

def rate_limit(f):
    """Rate limiting decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = request.remote_addr
        current_time = time.time()

        if client_ip in rate_limits:
            requests, reset_time = rate_limits[client_ip]
            if current_time < reset_time:
                if requests >= RATE_LIMIT_REQUESTS:
                    ERROR_COUNT.labels(type='rate_limit').inc()
                    return jsonify({'error': 'Rate limit exceeded'}), 429
                else:
                    rate_limits[client_ip] = (requests + 1, reset_time)
            else:
                rate_limits[client_ip] = (1, current_time + 60)
        else:
            rate_limits[client_ip] = (1, current_time + 60)

        return f(*args, **kwargs)
    return decorated_function

def cache_get(key, ttl_seconds):
    """Get cached result if still valid"""
    if key in request_cache:
        cache_time, data = request_cache[key]
        if time.time() - cache_time < ttl_seconds:
            return data
    return None

def cache_set(key, data):
    """Set cache entry with timestamp"""
    request_cache[key] = (time.time(), data)
    health_metrics['cache_size'] = len(request_cache)

def cleanup_cache():
    """Periodic cache cleanup"""
    while True:
        try:
            current_time = time.time()
            expired_keys = []

            for key, (cache_time, _) in request_cache.items():
                # Remove entries older than 10 minutes
                if current_time - cache_time > 600:
                    expired_keys.append(key)

            for key in expired_keys:
                del request_cache[key]

            health_metrics['cache_size'] = len(request_cache)

            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")

        time.sleep(300)  # Clean every 5 minutes

def api_health_check():
    """Periodic API health monitoring"""
    while True:
        try:
            start_time = time.time()
            price = connector.get_eth_price()
            response_time = time.time() - start_time

            health_metrics['last_api_check'] = datetime.now().isoformat()
            health_metrics['api_status'] = 'healthy'
            health_metrics['api_response_time'] = response_time

            ETHERSCAN_CALLS.labels(endpoint='price').inc()
            logger.info(f"API Health Check: {response_time:.3f}s - ETH: ${price['usd']:.2f}")

        except Exception as e:
            health_metrics['api_status'] = 'degraded'
            ERROR_COUNT.labels(type='health_check').inc()
            logger.warning(f"API Health Check Failed: {e}")

        time.sleep(60)  # Check every minute

# Start background threads
health_thread = threading.Thread(target=api_health_check, daemon=True)
health_thread.start()

cache_cleanup_thread = threading.Thread(target=cleanup_cache, daemon=True)
cache_cleanup_thread.start()

@app.before_request
def before_request():
    """Request preprocessing and metrics"""
    g.start_time = time.time()
    health_metrics['total_requests'] += 1
    ACTIVE_CONNECTIONS.inc()

@app.after_request
def after_request(response):
    """Response postprocessing and metrics"""
    response_time = time.time() - g.start_time

    # Add security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

    # Record metrics
    REQUEST_LATENCY.observe(response_time)
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.endpoint or 'unknown',
        status=response.status_code
    ).inc()

    ACTIVE_CONNECTIONS.dec()

    if response.status_code == 200:
        health_metrics['successful_requests'] += 1
    else:
        health_metrics['failed_requests'] += 1
        ERROR_COUNT.labels(type=f'http_{response.status_code}').inc()

    # Update average response time
    total_successful = health_metrics['successful_requests']
    if total_successful > 0:
        current_avg = health_metrics['avg_response_time']
        health_metrics['avg_response_time'] = (
            (current_avg * (total_successful - 1) + response_time) / total_successful
        )

    return response

@app.route('/health')
def health():
    """Comprehensive health check endpoint"""
    uptime = time.time() - health_metrics['start_time']

    return jsonify({
        'status': 'healthy' if health_metrics['api_status'] == 'healthy' else 'degraded',
        'uptime_seconds': uptime,
        'uptime_human': str(timedelta(seconds=int(uptime))),
        'metrics': health_metrics,
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/api/balance/<address>')
@rate_limit
def get_balance(address):
    """Get ETH balance with caching"""
    try:
        # Input validation
        if not address.startswith('0x') or len(address) != 42:
            ERROR_COUNT.labels(type='validation').inc()
            return jsonify({'error': 'Invalid Ethereum address'}), 400

        cache_key = f"balance_{address}"
        cached_result = cache_get(cache_key, cache_ttl['balance'])

        if cached_result:
            CACHE_HITS.labels(endpoint='balance').inc()
            return jsonify({'balance': cached_result, 'cached': True})

        balance = connector.get_eth_balance(address)
        cache_set(cache_key, balance)
        ETHERSCAN_CALLS.labels(endpoint='balance').inc()

        return jsonify({'balance': balance, 'cached': False})

    except Exception as e:
        ERROR_COUNT.labels(type='balance_error').inc()
        logger.error(f"Balance request failed for {address}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/price')
@rate_limit
def get_price():
    """Get ETH price with caching"""
    try:
        cached_result = cache_get('price', cache_ttl['price'])

        if cached_result:
            CACHE_HITS.labels(endpoint='price').inc()
            return jsonify({'price': cached_result, 'cached': True})

        price = connector.get_eth_price()
        cache_set('price', price)
        ETHERSCAN_CALLS.labels(endpoint='price').inc()

        return jsonify({'price': price, 'cached': False})

    except Exception as e:
        ERROR_COUNT.labels(type='price_error').inc()
        logger.error(f"Price request failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/gas')
@rate_limit
def get_gas():
    """Get gas prices with caching"""
    try:
        cached_result = cache_get('gas', cache_ttl['gas'])

        if cached_result:
            CACHE_HITS.labels(endpoint='gas').inc()
            return jsonify({'gas': cached_result, 'cached': True})

        gas = connector.get_gas_oracle()
        cache_set('gas', gas)
        ETHERSCAN_CALLS.labels(endpoint='gas').inc()

        return jsonify({'gas': gas, 'cached': False})

    except Exception as e:
        ERROR_COUNT.labels(type='gas_error').inc()
        logger.error(f"Gas request failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/transactions/<address>')
@rate_limit
def get_transactions(address):
    """Get recent transactions with caching"""
    try:
        # Input validation
        if not address.startswith('0x') or len(address) != 42:
            ERROR_COUNT.labels(type='validation').inc()
            return jsonify({'error': 'Invalid Ethereum address'}), 400

        cache_key = f"transactions_{address}"
        cached_result = cache_get(cache_key, cache_ttl['transactions'])

        if cached_result:
            CACHE_HITS.labels(endpoint='transactions').inc()
            return jsonify({'transactions': cached_result, 'cached': True})

        transactions = connector.get_transactions(address, offset=10)
        cache_set(cache_key, transactions)
        ETHERSCAN_CALLS.labels(endpoint='transactions').inc()

        return jsonify({'transactions': transactions, 'cached': False})

    except Exception as e:
        ERROR_COUNT.labels(type='transactions_error').inc()
        logger.error(f"Transactions request failed for {address}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/summary/<address>')
@rate_limit
def get_summary(address):
    """Get comprehensive address summary"""
    try:
        # Input validation
        if not address.startswith('0x') or len(address) != 42:
            ERROR_COUNT.labels(type='validation').inc()
            return jsonify({'error': 'Invalid Ethereum address'}), 400

        summary = connector.get_address_summary(address)
        ETHERSCAN_CALLS.labels(endpoint='summary').inc()
        return jsonify({'summary': summary})

    except Exception as e:
        ERROR_COUNT.labels(type='summary_error').inc()
        logger.error(f"Summary request failed for {address}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def get_status():
    """Get detailed service status"""
    return jsonify({
        'service': 'etherscan-api',
        'status': 'running',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat(),
        'metrics': {
            'total_requests': health_metrics['total_requests'],
            'success_rate': (health_metrics['successful_requests'] /
                           max(1, health_metrics['total_requests']) * 100),
            'avg_response_time': health_metrics['avg_response_time'],
            'cache_size': health_metrics['cache_size'],
            'api_status': health_metrics['api_status']
        }
    })

@app.errorhandler(404)
def not_found(error):
    """404 error handler"""
    ERROR_COUNT.labels(type='not_found').inc()
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """500 error handler"""
    ERROR_COUNT.labels(type='internal_error').inc()
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Ensure log directory exists
    os.makedirs('/app/logs', exist_ok=True)

    # Production server
    app.run(host='0.0.0.0', port=8080, debug=False)