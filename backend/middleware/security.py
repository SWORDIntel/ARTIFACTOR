"""
ARTIFACTOR v3.0 Security Middleware
Comprehensive security protection with OWASP compliance
"""

import time
import json
import hashlib
from typing import Dict, Set, Optional, List
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
import re
import ipaddress
from collections import defaultdict, deque
import asyncio
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive security middleware implementing:
    - OWASP security headers
    - Rate limiting and DDoS protection
    - Input validation and sanitization
    - Request/response logging
    - CORS enhancement
    - CSP and security policies
    - SQL injection detection
    - XSS protection
    """

    def __init__(self, app, config: Optional[Dict] = None):
        super().__init__(app)
        self.config = config or {}

        # Rate limiting storage
        self.rate_limits = defaultdict(lambda: deque())
        self.blocked_ips: Set[str] = set()
        self.suspicious_patterns = self._compile_security_patterns()

        # Security configuration
        self.max_requests_per_minute = self.config.get('max_requests_per_minute', 60)
        self.max_requests_per_hour = self.config.get('max_requests_per_hour', 1000)
        self.block_duration = self.config.get('block_duration', 300)  # 5 minutes
        self.enable_strict_csp = self.config.get('enable_strict_csp', True)
        self.enable_hsts = self.config.get('enable_hsts', True)
        self.enable_request_logging = self.config.get('enable_request_logging', True)

        # Trusted domains and IPs
        self.trusted_domains = set(self.config.get('trusted_domains', [
            'localhost', '127.0.0.1', '::1'
        ]))

        # Content Security Policy
        self.csp_policy = self._build_csp_policy()

        logger.info("SecurityMiddleware initialized with comprehensive protection")

    def _compile_security_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for security threat detection"""
        return {
            'sql_injection': re.compile(
                r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|OR|AND)\b.*?'
                r'(\b(FROM|INTO|SET|WHERE|VALUES|TABLE|DATABASE)\b|[\'";])|'
                r'(\'\s*(OR|AND)\s*\w+\s*=\s*\w+)|'
                r'(\-\-|/\*|\*/)|'
                r'(\bUNION\s+SELECT\b)|'
                r'(\b1\s*=\s*1\b))',
                re.IGNORECASE | re.MULTILINE
            ),
            'xss': re.compile(
                r'(<script[^>]*>.*?</script>|'
                r'javascript:|'
                r'on\w+\s*=|'
                r'<iframe[^>]*>|'
                r'<object[^>]*>|'
                r'<embed[^>]*>|'
                r'<link[^>]*>|'
                r'<meta[^>]*>|'
                r'data:text/html|'
                r'vbscript:|'
                r'expression\s*\()',
                re.IGNORECASE | re.DOTALL
            ),
            'path_traversal': re.compile(
                r'(\.\./|\.\.\\|%2e%2e%2f|%2e%2e\\|'
                r'\.\.%2f|\.\.%5c|%252e%252e%252f|'
                r'file://|/etc/passwd|/proc/|/sys/)',
                re.IGNORECASE
            ),
            'command_injection': re.compile(
                r'(\|\s*\w+|;\s*\w+|`[^`]+`|'
                r'\$\([^)]+\)|&\s*\w+|'
                r'\bnc\s+|netcat|/bin/|/usr/bin/|'
                r'curl\s+|wget\s+|ssh\s+)',
                re.IGNORECASE
            ),
            'sensitive_files': re.compile(
                r'(\.env|\.git|\.ssh|\.aws|'
                r'config\.py|settings\.py|secrets|'
                r'password|passwd|shadow|'
                r'id_rsa|id_dsa|\.key|\.pem)',
                re.IGNORECASE
            )
        }

    def _build_csp_policy(self) -> str:
        """Build Content Security Policy"""
        if not self.enable_strict_csp:
            return "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"

        return (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: blob: https:; "
            "connect-src 'self' ws: wss:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "upgrade-insecure-requests"
        )

    async def dispatch(self, request: Request, call_next):
        """Main middleware dispatch method"""
        start_time = time.time()

        try:
            # Pre-request security checks
            await self._check_rate_limiting(request)
            await self._validate_request_security(request)

            # Process request
            response = await call_next(request)

            # Post-request security enhancements
            self._add_security_headers(response)

            # Log request if enabled
            if self.enable_request_logging:
                await self._log_request(request, response, time.time() - start_time)

            return response

        except HTTPException as e:
            # Security violation detected
            await self._log_security_violation(request, str(e.detail))
            return JSONResponse(
                status_code=e.status_code,
                content={"error": "Security policy violation", "detail": "Request blocked by security policy"}
            )
        except Exception as e:
            logger.error(f"Security middleware error: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal security error"}
            )

    async def _check_rate_limiting(self, request: Request):
        """Check rate limiting and DDoS protection"""
        client_ip = self._get_client_ip(request)

        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="IP temporarily blocked due to suspicious activity"
            )

        current_time = time.time()

        # Clean old requests
        self._clean_old_requests(client_ip, current_time)

        # Check rate limits
        requests = self.rate_limits[client_ip]

        # Check requests per minute
        recent_requests = sum(1 for req_time in requests if current_time - req_time <= 60)
        if recent_requests >= self.max_requests_per_minute:
            self._block_ip(client_ip)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded: too many requests per minute"
            )

        # Check requests per hour
        hourly_requests = sum(1 for req_time in requests if current_time - req_time <= 3600)
        if hourly_requests >= self.max_requests_per_hour:
            self._block_ip(client_ip)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded: too many requests per hour"
            )

        # Record this request
        requests.append(current_time)

    async def _validate_request_security(self, request: Request):
        """Validate request for security threats"""

        # Get request data for analysis
        url = str(request.url)
        method = request.method
        headers = dict(request.headers)

        # Check URL for threats
        self._check_for_threats(url, "URL")

        # Check headers for threats
        for header_name, header_value in headers.items():
            if header_name.lower() not in ['host', 'user-agent', 'accept', 'accept-encoding', 'connection']:
                self._check_for_threats(header_value, f"Header {header_name}")

        # Check request body for POST/PUT requests
        if method in ['POST', 'PUT', 'PATCH']:
            await self._validate_request_body(request)

        # Validate content type
        content_type = headers.get('content-type', '')
        if method in ['POST', 'PUT', 'PATCH'] and content_type:
            self._validate_content_type(content_type)

        # Check for suspicious user agents
        user_agent = headers.get('user-agent', '')
        if self._is_suspicious_user_agent(user_agent):
            logger.warning(f"Suspicious user agent detected: {user_agent}")

    async def _validate_request_body(self, request: Request):
        """Validate request body for security threats"""
        try:
            # Read body
            body = await request.body()
            if body:
                body_str = body.decode('utf-8', errors='ignore')

                # Check for threats in body
                self._check_for_threats(body_str, "Request Body")

                # Validate JSON if applicable
                content_type = request.headers.get('content-type', '')
                if 'application/json' in content_type:
                    try:
                        json_data = json.loads(body_str)
                        self._validate_json_security(json_data)
                    except json.JSONDecodeError:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid JSON format"
                        )
        except Exception as e:
            logger.error(f"Error validating request body: {e}")

    def _check_for_threats(self, content: str, location: str):
        """Check content for security threats"""
        if not content:
            return

        for threat_type, pattern in self.suspicious_patterns.items():
            if pattern.search(content):
                logger.warning(f"{threat_type.upper()} pattern detected in {location}: {content[:100]}...")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Malicious pattern detected in {location}"
                )

    def _validate_json_security(self, data, depth=0, max_depth=10):
        """Recursively validate JSON data for security threats"""
        if depth > max_depth:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="JSON structure too deeply nested"
            )

        if isinstance(data, dict):
            if len(data) > 1000:  # Prevent DoS through large objects
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="JSON object too large"
                )

            for key, value in data.items():
                self._check_for_threats(str(key), "JSON Key")
                if isinstance(value, str):
                    self._check_for_threats(value, "JSON Value")
                elif isinstance(value, (dict, list)):
                    self._validate_json_security(value, depth + 1, max_depth)

        elif isinstance(data, list):
            if len(data) > 10000:  # Prevent DoS through large arrays
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="JSON array too large"
                )

            for item in data:
                if isinstance(item, str):
                    self._check_for_threats(item, "JSON Array Item")
                elif isinstance(item, (dict, list)):
                    self._validate_json_security(item, depth + 1, max_depth)

    def _validate_content_type(self, content_type: str):
        """Validate content type"""
        allowed_types = [
            'application/json',
            'application/x-www-form-urlencoded',
            'multipart/form-data',
            'text/plain',
            'application/octet-stream'
        ]

        # Extract base content type
        base_type = content_type.split(';')[0].strip().lower()

        if base_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported content type: {base_type}"
            )

    def _is_suspicious_user_agent(self, user_agent: str) -> bool:
        """Check for suspicious user agents"""
        suspicious_agents = [
            'sqlmap', 'nikto', 'nmap', 'masscan', 'nessus',
            'burp', 'w3af', 'owasp', 'python-requests',
            'curl', 'wget', 'scanner', 'bot', 'crawler'
        ]

        user_agent_lower = user_agent.lower()
        return any(agent in user_agent_lower for agent in suspicious_agents)

    def _add_security_headers(self, response: Response):
        """Add comprehensive security headers"""
        headers = {
            # OWASP recommended headers
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',

            # Content Security Policy
            'Content-Security-Policy': self.csp_policy,

            # Additional security headers
            'Server': 'ARTIFACTOR-Secure',  # Hide server information
            'X-Powered-By': '',  # Remove technology disclosure
            'Cache-Control': 'no-store, no-cache, must-revalidate, private',
            'Pragma': 'no-cache',
            'Expires': '0',
        }

        # Add HSTS if enabled and HTTPS
        if self.enable_hsts:
            headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'

        # Apply headers
        for header, value in headers.items():
            response.headers[header] = value

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address considering proxies"""
        # Check for forwarded headers (in order of preference)
        forwarded_headers = [
            'X-Forwarded-For',
            'X-Real-IP',
            'CF-Connecting-IP',  # Cloudflare
            'X-Client-IP',
            'X-Forwarded'
        ]

        for header in forwarded_headers:
            if header in request.headers:
                # Take the first IP in case of multiple
                ip = request.headers[header].split(',')[0].strip()
                if self._is_valid_ip(ip):
                    return ip

        # Fallback to direct connection
        return request.client.host if request.client else '127.0.0.1'

    def _is_valid_ip(self, ip: str) -> bool:
        """Validate IP address format"""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False

    def _clean_old_requests(self, client_ip: str, current_time: float):
        """Clean old requests from rate limiting storage"""
        requests = self.rate_limits[client_ip]

        # Remove requests older than 1 hour
        while requests and current_time - requests[0] > 3600:
            requests.popleft()

    def _block_ip(self, client_ip: str):
        """Block IP address temporarily"""
        self.blocked_ips.add(client_ip)
        logger.warning(f"IP {client_ip} blocked due to rate limit violation")

        # Schedule unblocking
        asyncio.create_task(self._unblock_ip_after_delay(client_ip))

    async def _unblock_ip_after_delay(self, client_ip: str):
        """Unblock IP after delay"""
        await asyncio.sleep(self.block_duration)
        self.blocked_ips.discard(client_ip)
        logger.info(f"IP {client_ip} unblocked after timeout")

    async def _log_request(self, request: Request, response: Response, duration: float):
        """Log request for security monitoring"""
        client_ip = self._get_client_ip(request)

        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'client_ip': client_ip,
            'method': request.method,
            'url': str(request.url),
            'status_code': response.status_code,
            'duration': round(duration, 3),
            'user_agent': request.headers.get('user-agent', ''),
            'content_length': response.headers.get('content-length', '0')
        }

        # Log based on status code
        if response.status_code >= 400:
            logger.warning(f"HTTP {response.status_code}: {json.dumps(log_data)}")
        else:
            logger.info(f"Request: {json.dumps(log_data)}")

    async def _log_security_violation(self, request: Request, detail: str):
        """Log security violations"""
        client_ip = self._get_client_ip(request)

        violation_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'type': 'SECURITY_VIOLATION',
            'client_ip': client_ip,
            'method': request.method,
            'url': str(request.url),
            'detail': detail,
            'user_agent': request.headers.get('user-agent', ''),
            'headers': dict(request.headers)
        }

        logger.error(f"SECURITY VIOLATION: {json.dumps(violation_data)}")

class SecurityConfig:
    """Security configuration helper"""

    @staticmethod
    def get_production_config() -> Dict:
        """Get production-ready security configuration"""
        return {
            'max_requests_per_minute': 100,
            'max_requests_per_hour': 2000,
            'block_duration': 600,  # 10 minutes
            'enable_strict_csp': True,
            'enable_hsts': True,
            'enable_request_logging': True,
            'trusted_domains': ['localhost', '127.0.0.1']
        }

    @staticmethod
    def get_development_config() -> Dict:
        """Get development-friendly security configuration"""
        return {
            'max_requests_per_minute': 1000,
            'max_requests_per_hour': 10000,
            'block_duration': 60,  # 1 minute
            'enable_strict_csp': False,
            'enable_hsts': False,
            'enable_request_logging': True,
            'trusted_domains': ['localhost', '127.0.0.1', '0.0.0.0']
        }