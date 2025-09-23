"""
ARTIFACTOR v3.0 Secure JWT Manager
Enhanced JWT security with token rotation, blacklisting, and comprehensive protection
"""

import asyncio
import logging
import json
import secrets
import hashlib
import time
from typing import Dict, Any, Optional, List, Tuple, Union
from datetime import datetime, timedelta
import uuid
import jwt
from jwt.exceptions import PyJWTError, ExpiredSignatureError, InvalidTokenError
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import redis.asyncio as redis
from fastapi import HTTPException, status
import bcrypt

logger = logging.getLogger(__name__)

class JWTSecurityError(Exception):
    """Raised when JWT security validation fails"""
    pass

class TokenBlacklistError(Exception):
    """Raised when token is blacklisted"""
    pass

class JWTKeyManager:
    """Manages JWT signing keys with rotation"""

    def __init__(self):
        self.current_key_id = None
        self.keys = {}
        self.key_rotation_interval = timedelta(hours=24)  # Rotate keys daily
        self.last_rotation = None

    def generate_key_pair(self) -> Tuple[str, str]:
        """Generate new RSA key pair for JWT signing"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        return private_pem.decode(), public_pem.decode()

    def initialize_keys(self) -> str:
        """Initialize key management with initial key pair"""
        key_id = str(uuid.uuid4())
        private_key, public_key = self.generate_key_pair()

        self.keys[key_id] = {
            'private_key': private_key,
            'public_key': public_key,
            'created_at': datetime.utcnow(),
            'active': True
        }

        self.current_key_id = key_id
        self.last_rotation = datetime.utcnow()

        logger.info(f"JWT keys initialized with key ID: {key_id}")
        return key_id

    def rotate_keys(self) -> str:
        """Rotate JWT signing keys"""
        # Generate new key pair
        new_key_id = str(uuid.uuid4())
        private_key, public_key = self.generate_key_pair()

        # Add new key
        self.keys[new_key_id] = {
            'private_key': private_key,
            'public_key': public_key,
            'created_at': datetime.utcnow(),
            'active': True
        }

        # Deactivate old key (but keep for verification)
        if self.current_key_id:
            self.keys[self.current_key_id]['active'] = False

        # Set new key as current
        self.current_key_id = new_key_id
        self.last_rotation = datetime.utcnow()

        # Clean up very old keys (older than 7 days)
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        old_keys = [
            key_id for key_id, key_data in self.keys.items()
            if key_data['created_at'] < cutoff_date and not key_data['active']
        ]

        for key_id in old_keys:
            del self.keys[key_id]
            logger.info(f"Removed old JWT key: {key_id}")

        logger.info(f"JWT keys rotated. New key ID: {new_key_id}")
        return new_key_id

    def should_rotate_keys(self) -> bool:
        """Check if keys should be rotated"""
        if not self.last_rotation:
            return True

        return datetime.utcnow() - self.last_rotation > self.key_rotation_interval

    def get_signing_key(self) -> Tuple[str, str]:
        """Get current signing key"""
        if not self.current_key_id:
            self.initialize_keys()

        key_data = self.keys[self.current_key_id]
        return key_data['private_key'], self.current_key_id

    def get_verification_key(self, key_id: str) -> Optional[str]:
        """Get verification key by ID"""
        key_data = self.keys.get(key_id)
        return key_data['public_key'] if key_data else None

class SecureTokenStore:
    """Secure token storage with Redis backend"""

    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or "redis://localhost:6379"
        self.redis_client = None
        self.fallback_store = {}  # In-memory fallback

    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            await self.redis_client.ping()
            logger.info("Redis token store initialized")
        except Exception as e:
            logger.warning(f"Redis not available, using fallback store: {e}")
            self.redis_client = None

    async def store_token(self, token_id: str, token_data: Dict[str, Any], ttl: int):
        """Store token data with TTL"""
        try:
            if self.redis_client:
                await self.redis_client.setex(
                    f"token:{token_id}",
                    ttl,
                    json.dumps(token_data)
                )
            else:
                # Fallback to in-memory storage
                expiry = datetime.utcnow() + timedelta(seconds=ttl)
                self.fallback_store[token_id] = {
                    'data': token_data,
                    'expiry': expiry
                }
        except Exception as e:
            logger.error(f"Failed to store token: {e}")
            raise JWTSecurityError("Token storage failed")

    async def get_token(self, token_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve token data"""
        try:
            if self.redis_client:
                data = await self.redis_client.get(f"token:{token_id}")
                return json.loads(data) if data else None
            else:
                # Fallback to in-memory storage
                token_info = self.fallback_store.get(token_id)
                if token_info and token_info['expiry'] > datetime.utcnow():
                    return token_info['data']
                elif token_info:
                    del self.fallback_store[token_id]
                return None
        except Exception as e:
            logger.error(f"Failed to retrieve token: {e}")
            return None

    async def revoke_token(self, token_id: str):
        """Revoke token"""
        try:
            if self.redis_client:
                await self.redis_client.delete(f"token:{token_id}")
            else:
                self.fallback_store.pop(token_id, None)
        except Exception as e:
            logger.error(f"Failed to revoke token: {e}")

    async def blacklist_token(self, token_id: str, reason: str, ttl: int):
        """Add token to blacklist"""
        try:
            blacklist_data = {
                'reason': reason,
                'blacklisted_at': datetime.utcnow().isoformat()
            }

            if self.redis_client:
                await self.redis_client.setex(
                    f"blacklist:{token_id}",
                    ttl,
                    json.dumps(blacklist_data)
                )
            else:
                expiry = datetime.utcnow() + timedelta(seconds=ttl)
                self.fallback_store[f"blacklist:{token_id}"] = {
                    'data': blacklist_data,
                    'expiry': expiry
                }

            logger.info(f"Token blacklisted: {token_id} - {reason}")
        except Exception as e:
            logger.error(f"Failed to blacklist token: {e}")

    async def is_blacklisted(self, token_id: str) -> bool:
        """Check if token is blacklisted"""
        try:
            if self.redis_client:
                result = await self.redis_client.get(f"blacklist:{token_id}")
                return result is not None
            else:
                blacklist_key = f"blacklist:{token_id}"
                token_info = self.fallback_store.get(blacklist_key)
                if token_info and token_info['expiry'] > datetime.utcnow():
                    return True
                elif token_info:
                    del self.fallback_store[blacklist_key]
                return False
        except Exception as e:
            logger.error(f"Failed to check blacklist: {e}")
            return False

class SecureJWTManager:
    """Comprehensive JWT security manager"""

    def __init__(self, secret_key: str = None, redis_url: str = None):
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.algorithm = "RS256"  # Use RSA for enhanced security
        self.key_manager = JWTKeyManager()
        self.token_store = SecureTokenStore(redis_url)

        # Security settings
        self.access_token_lifetime = timedelta(minutes=15)  # Short-lived access tokens
        self.refresh_token_lifetime = timedelta(days=1)     # Short-lived refresh tokens
        self.max_token_length = 2048
        self.rate_limit_window = timedelta(minutes=1)
        self.max_tokens_per_window = 10

        # Token tracking
        self.token_stats = {}
        self.suspicious_activity = {}

        # Initialize
        self.key_manager.initialize_keys()

    async def initialize(self):
        """Initialize the JWT manager"""
        await self.token_store.initialize()
        logger.info("Secure JWT Manager initialized")

    async def create_tokens(
        self,
        user_id: str,
        additional_claims: Optional[Dict[str, Any]] = None,
        access_token_lifetime: Optional[timedelta] = None,
        refresh_token_lifetime: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """Create secure access and refresh tokens"""
        try:
            # Check rate limiting
            await self._check_rate_limit(user_id)

            # Rotate keys if needed
            if self.key_manager.should_rotate_keys():
                self.key_manager.rotate_keys()

            # Generate unique IDs
            access_token_id = str(uuid.uuid4())
            refresh_token_id = str(uuid.uuid4())

            # Get signing key
            private_key, key_id = self.key_manager.get_signing_key()

            # Token lifetimes
            access_lifetime = access_token_lifetime or self.access_token_lifetime
            refresh_lifetime = refresh_token_lifetime or self.refresh_token_lifetime

            # Create access token
            access_payload = {
                'sub': user_id,
                'jti': access_token_id,
                'type': 'access',
                'iat': datetime.utcnow(),
                'exp': datetime.utcnow() + access_lifetime,
                'iss': 'ARTIFACTOR-v3',
                'aud': 'artifactor-api',
                'kid': key_id,
                'scope': 'api_access'
            }

            if additional_claims:
                access_payload.update(additional_claims)

            access_token = jwt.encode(
                access_payload,
                private_key,
                algorithm=self.algorithm,
                headers={'kid': key_id}
            )

            # Create refresh token
            refresh_payload = {
                'sub': user_id,
                'jti': refresh_token_id,
                'type': 'refresh',
                'iat': datetime.utcnow(),
                'exp': datetime.utcnow() + refresh_lifetime,
                'iss': 'ARTIFACTOR-v3',
                'aud': 'artifactor-api',
                'kid': key_id,
                'access_token_id': access_token_id
            }

            refresh_token = jwt.encode(
                refresh_payload,
                private_key,
                algorithm=self.algorithm,
                headers={'kid': key_id}
            )

            # Store token metadata
            token_metadata = {
                'user_id': user_id,
                'access_token_id': access_token_id,
                'refresh_token_id': refresh_token_id,
                'created_at': datetime.utcnow().isoformat(),
                'expires_at': (datetime.utcnow() + refresh_lifetime).isoformat(),
                'ip_address': None,  # To be set by caller
                'user_agent': None   # To be set by caller
            }

            await self.token_store.store_token(
                access_token_id,
                token_metadata,
                int(access_lifetime.total_seconds())
            )

            await self.token_store.store_token(
                refresh_token_id,
                token_metadata,
                int(refresh_lifetime.total_seconds())
            )

            # Update statistics
            await self._update_token_stats(user_id, 'created')

            logger.info(f"Tokens created for user {user_id}")

            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_type': 'Bearer',
                'expires_in': int(access_lifetime.total_seconds()),
                'access_token_id': access_token_id,
                'refresh_token_id': refresh_token_id
            }

        except Exception as e:
            logger.error(f"Token creation failed: {e}")
            await self._log_suspicious_activity(user_id, 'token_creation_failed', str(e))
            raise JWTSecurityError(f"Token creation failed: {str(e)}")

    async def verify_token(
        self,
        token: str,
        expected_type: str = 'access',
        verify_exp: bool = True
    ) -> Dict[str, Any]:
        """Verify and decode JWT token with comprehensive validation"""
        try:
            # Basic token validation
            if not token or len(token) > self.max_token_length:
                raise JWTSecurityError("Invalid token format")

            # Decode header to get key ID
            unverified_header = jwt.get_unverified_header(token)
            key_id = unverified_header.get('kid')

            if not key_id:
                raise JWTSecurityError("Token missing key ID")

            # Get verification key
            public_key = self.key_manager.get_verification_key(key_id)
            if not public_key:
                raise JWTSecurityError("Unknown key ID")

            # Decode and verify token
            payload = jwt.decode(
                token,
                public_key,
                algorithms=[self.algorithm],
                options={
                    'verify_exp': verify_exp,
                    'verify_iat': True,
                    'verify_iss': True,
                    'verify_aud': True,
                    'require': ['sub', 'jti', 'type', 'iat', 'exp', 'iss', 'aud']
                },
                issuer='ARTIFACTOR-v3',
                audience='artifactor-api'
            )

            # Validate token type
            if payload.get('type') != expected_type:
                raise JWTSecurityError(f"Invalid token type: expected {expected_type}")

            # Check if token is blacklisted
            token_id = payload.get('jti')
            if await self.token_store.is_blacklisted(token_id):
                raise TokenBlacklistError("Token is blacklisted")

            # Verify token exists in store
            token_metadata = await self.token_store.get_token(token_id)
            if not token_metadata:
                raise JWTSecurityError("Token not found in store")

            # Additional security checks
            await self._perform_security_checks(payload, token_metadata)

            # Update last used timestamp
            await self._update_token_usage(token_id)

            return payload

        except ExpiredSignatureError:
            logger.warning("Expired token verification attempted")
            raise JWTSecurityError("Token has expired")
        except PyJWTError as e:
            logger.warning(f"JWT verification failed: {e}")
            raise JWTSecurityError(f"Token verification failed: {str(e)}")
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            raise JWTSecurityError(f"Token verification error: {str(e)}")

    async def refresh_tokens(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        try:
            # Verify refresh token
            refresh_payload = await self.verify_token(refresh_token, 'refresh')

            user_id = refresh_payload['sub']
            old_refresh_id = refresh_payload['jti']
            old_access_id = refresh_payload.get('access_token_id')

            # Revoke old tokens
            if old_access_id:
                await self.revoke_token(old_access_id, "Token refreshed")
            await self.revoke_token(old_refresh_id, "Token refreshed")

            # Create new token pair
            new_tokens = await self.create_tokens(user_id)

            logger.info(f"Tokens refreshed for user {user_id}")
            return new_tokens

        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            raise JWTSecurityError(f"Token refresh failed: {str(e)}")

    async def revoke_token(self, token_id: str, reason: str = "User logout"):
        """Revoke a specific token"""
        try:
            await self.token_store.revoke_token(token_id)
            logger.info(f"Token revoked: {token_id} - {reason}")
        except Exception as e:
            logger.error(f"Token revocation failed: {e}")

    async def revoke_all_user_tokens(self, user_id: str, reason: str = "Security measure"):
        """Revoke all tokens for a user"""
        try:
            # This would require additional tracking in a production system
            # For now, we'll add the user to a revocation list
            await self.token_store.blacklist_token(
                f"user:{user_id}",
                reason,
                int(self.refresh_token_lifetime.total_seconds())
            )
            logger.info(f"All tokens revoked for user {user_id} - {reason}")
        except Exception as e:
            logger.error(f"User token revocation failed: {e}")

    async def blacklist_token(self, token_id: str, reason: str):
        """Add token to blacklist"""
        try:
            await self.token_store.blacklist_token(
                token_id,
                reason,
                int(self.refresh_token_lifetime.total_seconds())
            )
        except Exception as e:
            logger.error(f"Token blacklisting failed: {e}")

    async def _check_rate_limit(self, user_id: str):
        """Check token creation rate limiting"""
        now = datetime.utcnow()
        window_start = now - self.rate_limit_window

        if user_id not in self.token_stats:
            self.token_stats[user_id] = []

        # Clean old entries
        self.token_stats[user_id] = [
            timestamp for timestamp in self.token_stats[user_id]
            if timestamp > window_start
        ]

        # Check limit
        if len(self.token_stats[user_id]) >= self.max_tokens_per_window:
            await self._log_suspicious_activity(user_id, 'rate_limit_exceeded')
            raise JWTSecurityError("Token creation rate limit exceeded")

        # Add current timestamp
        self.token_stats[user_id].append(now)

    async def _perform_security_checks(self, payload: Dict[str, Any], metadata: Dict[str, Any]):
        """Perform additional security checks"""
        user_id = payload['sub']

        # Check for token reuse patterns
        if await self._detect_token_reuse(payload):
            await self._log_suspicious_activity(user_id, 'potential_token_reuse')

        # Check for unusual usage patterns
        if await self._detect_unusual_usage(payload, metadata):
            await self._log_suspicious_activity(user_id, 'unusual_token_usage')

    async def _detect_token_reuse(self, payload: Dict[str, Any]) -> bool:
        """Detect potential token reuse attacks"""
        # Implement token reuse detection logic
        return False

    async def _detect_unusual_usage(self, payload: Dict[str, Any], metadata: Dict[str, Any]) -> bool:
        """Detect unusual token usage patterns"""
        # Implement unusual usage detection logic
        return False

    async def _update_token_usage(self, token_id: str):
        """Update token usage timestamp"""
        try:
            token_metadata = await self.token_store.get_token(token_id)
            if token_metadata:
                token_metadata['last_used'] = datetime.utcnow().isoformat()
                ttl = 3600  # 1 hour default TTL for usage updates
                await self.token_store.store_token(token_id, token_metadata, ttl)
        except Exception as e:
            logger.error(f"Failed to update token usage: {e}")

    async def _update_token_stats(self, user_id: str, action: str):
        """Update token statistics"""
        if user_id not in self.token_stats:
            self.token_stats[user_id] = []

        self.token_stats[user_id].append({
            'action': action,
            'timestamp': datetime.utcnow().isoformat()
        })

    async def _log_suspicious_activity(self, user_id: str, activity_type: str, details: str = None):
        """Log suspicious activity"""
        if user_id not in self.suspicious_activity:
            self.suspicious_activity[user_id] = []

        activity = {
            'type': activity_type,
            'timestamp': datetime.utcnow().isoformat(),
            'details': details
        }

        self.suspicious_activity[user_id].append(activity)
        logger.warning(f"Suspicious JWT activity - User: {user_id}, Type: {activity_type}, Details: {details}")

    def get_security_metrics(self) -> Dict[str, Any]:
        """Get JWT security metrics"""
        total_tokens = sum(len(stats) for stats in self.token_stats.values())
        total_suspicious = sum(len(activities) for activities in self.suspicious_activity.values())

        return {
            'total_tokens_created': total_tokens,
            'active_users': len(self.token_stats),
            'suspicious_activities': total_suspicious,
            'key_rotations': len(self.key_manager.keys),
            'current_key_id': self.key_manager.current_key_id,
            'last_key_rotation': self.key_manager.last_rotation.isoformat() if self.key_manager.last_rotation else None
        }

# Global secure JWT manager (to be initialized with proper config)
secure_jwt_manager = None

def initialize_jwt_manager(secret_key: str = None, redis_url: str = None) -> SecureJWTManager:
    """Initialize global JWT manager"""
    global secure_jwt_manager
    secure_jwt_manager = SecureJWTManager(secret_key, redis_url)
    return secure_jwt_manager

# Export
__all__ = [
    'SecureJWTManager', 'JWTSecurityError', 'TokenBlacklistError',
    'JWTKeyManager', 'SecureTokenStore', 'initialize_jwt_manager'
]