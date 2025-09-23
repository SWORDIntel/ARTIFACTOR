"""
ARTIFACTOR v3.0 Security Monitoring System
Comprehensive security event logging, monitoring, and alerting
"""

import asyncio
import logging
import json
import time
import hashlib
import smtplib
import ssl
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import aiofiles
import aiohttp
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import redis.asyncio as redis
from collections import defaultdict, deque
import threading
import sqlite3

logger = logging.getLogger(__name__)

class SecurityEventType(Enum):
    """Security event types"""
    AUTHENTICATION_FAILED = "authentication_failed"
    AUTHENTICATION_SUCCESS = "authentication_success"
    AUTHORIZATION_DENIED = "authorization_denied"
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    XSS_ATTEMPT = "xss_attempt"
    COMMAND_INJECTION_ATTEMPT = "command_injection_attempt"
    PATH_TRAVERSAL_ATTEMPT = "path_traversal_attempt"
    FILE_UPLOAD_VIRUS = "file_upload_virus"
    FILE_UPLOAD_BLOCKED = "file_upload_blocked"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_USER_AGENT = "suspicious_user_agent"
    PLUGIN_SECURITY_VIOLATION = "plugin_security_violation"
    JWT_TOKEN_ABUSE = "jwt_token_abuse"
    BRUTE_FORCE_ATTACK = "brute_force_attack"
    PRIVILEGE_ESCALATION_ATTEMPT = "privilege_escalation_attempt"
    DATA_EXFILTRATION_ATTEMPT = "data_exfiltration_attempt"
    SYSTEM_COMPROMISE_INDICATOR = "system_compromise_indicator"
    ANOMALOUS_BEHAVIOR = "anomalous_behavior"

class SecuritySeverity(Enum):
    """Security severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SecurityEvent:
    """Security event data structure"""
    event_id: str
    event_type: SecurityEventType
    severity: SecuritySeverity
    timestamp: datetime
    user_id: Optional[str]
    ip_address: str
    user_agent: str
    request_path: str
    details: Dict[str, Any]
    threat_score: float
    mitigated: bool = False
    mitigation_action: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'severity': self.severity.value,
            'timestamp': self.timestamp.isoformat(),
            'user_id': self.user_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'request_path': self.request_path,
            'details': self.details,
            'threat_score': self.threat_score,
            'mitigated': self.mitigated,
            'mitigation_action': self.mitigation_action
        }

class ThreatScorer:
    """Calculate threat scores for security events"""

    def __init__(self):
        self.base_scores = {
            SecurityEventType.AUTHENTICATION_FAILED: 3.0,
            SecurityEventType.AUTHENTICATION_SUCCESS: 0.0,
            SecurityEventType.AUTHORIZATION_DENIED: 5.0,
            SecurityEventType.SQL_INJECTION_ATTEMPT: 9.0,
            SecurityEventType.XSS_ATTEMPT: 7.0,
            SecurityEventType.COMMAND_INJECTION_ATTEMPT: 9.5,
            SecurityEventType.PATH_TRAVERSAL_ATTEMPT: 8.0,
            SecurityEventType.FILE_UPLOAD_VIRUS: 9.0,
            SecurityEventType.FILE_UPLOAD_BLOCKED: 6.0,
            SecurityEventType.RATE_LIMIT_EXCEEDED: 4.0,
            SecurityEventType.SUSPICIOUS_USER_AGENT: 3.0,
            SecurityEventType.PLUGIN_SECURITY_VIOLATION: 8.5,
            SecurityEventType.JWT_TOKEN_ABUSE: 7.5,
            SecurityEventType.BRUTE_FORCE_ATTACK: 8.0,
            SecurityEventType.PRIVILEGE_ESCALATION_ATTEMPT: 9.5,
            SecurityEventType.DATA_EXFILTRATION_ATTEMPT: 9.0,
            SecurityEventType.SYSTEM_COMPROMISE_INDICATOR: 10.0,
            SecurityEventType.ANOMALOUS_BEHAVIOR: 5.0
        }

    def calculate_score(
        self,
        event_type: SecurityEventType,
        details: Dict[str, Any],
        user_history: Optional[Dict[str, Any]] = None
    ) -> float:
        """Calculate threat score for security event"""
        base_score = self.base_scores.get(event_type, 5.0)

        # Apply modifiers based on details
        modifiers = []

        # IP reputation modifier
        if self._is_suspicious_ip(details.get('ip_address', '')):
            modifiers.append(2.0)

        # Frequency modifier
        if details.get('frequency', 0) > 10:
            modifiers.append(1.5)

        # User agent modifier
        if self._is_suspicious_user_agent(details.get('user_agent', '')):
            modifiers.append(1.2)

        # Geographic anomaly modifier
        if details.get('geographic_anomaly', False):
            modifiers.append(1.3)

        # Time-based anomaly modifier
        if details.get('time_anomaly', False):
            modifiers.append(1.2)

        # User history modifier
        if user_history and user_history.get('previous_violations', 0) > 0:
            modifiers.append(1.0 + (user_history['previous_violations'] * 0.1))

        # Apply modifiers
        final_score = base_score
        for modifier in modifiers:
            final_score *= modifier

        # Cap at 10.0
        return min(final_score, 10.0)

    def _is_suspicious_ip(self, ip_address: str) -> bool:
        """Check if IP address is suspicious"""
        # In production, this would check against threat intelligence feeds
        suspicious_ranges = [
            '10.0.0.0/8',    # Private ranges might be suspicious in certain contexts
            '172.16.0.0/12',
            '192.168.0.0/16'
        ]
        # Simplified check - in production use proper IP range checking
        return any(ip_address.startswith(range_prefix.split('/')[0][:7])
                  for range_prefix in suspicious_ranges)

    def _is_suspicious_user_agent(self, user_agent: str) -> bool:
        """Check if user agent is suspicious"""
        suspicious_patterns = [
            'bot', 'crawler', 'scanner', 'curl', 'wget', 'python',
            'sqlmap', 'nikto', 'nmap', 'masscan', 'burp'
        ]
        return any(pattern in user_agent.lower() for pattern in suspicious_patterns)

class SecurityEventAggregator:
    """Aggregate and correlate security events"""

    def __init__(self, time_window: int = 300):  # 5 minutes
        self.time_window = time_window
        self.event_buckets = defaultdict(lambda: defaultdict(list))
        self.correlation_rules = self._load_correlation_rules()

    def _load_correlation_rules(self) -> List[Dict[str, Any]]:
        """Load event correlation rules"""
        return [
            {
                'name': 'Brute Force Attack',
                'events': [SecurityEventType.AUTHENTICATION_FAILED],
                'threshold': 5,
                'window': 300,
                'groupby': ['ip_address'],
                'output_event': SecurityEventType.BRUTE_FORCE_ATTACK
            },
            {
                'name': 'Multi-Vector Attack',
                'events': [
                    SecurityEventType.SQL_INJECTION_ATTEMPT,
                    SecurityEventType.XSS_ATTEMPT,
                    SecurityEventType.COMMAND_INJECTION_ATTEMPT
                ],
                'threshold': 3,
                'window': 600,
                'groupby': ['ip_address'],
                'output_event': SecurityEventType.SYSTEM_COMPROMISE_INDICATOR
            },
            {
                'name': 'Privilege Escalation Sequence',
                'events': [
                    SecurityEventType.AUTHORIZATION_DENIED,
                    SecurityEventType.PLUGIN_SECURITY_VIOLATION
                ],
                'threshold': 2,
                'window': 180,
                'groupby': ['user_id'],
                'output_event': SecurityEventType.PRIVILEGE_ESCALATION_ATTEMPT
            }
        ]

    def aggregate_event(self, event: SecurityEvent) -> List[SecurityEvent]:
        """Aggregate event and check for correlation patterns"""
        now = datetime.utcnow()
        correlated_events = []

        # Add event to buckets
        for rule in self.correlation_rules:
            if event.event_type in rule['events']:
                # Create grouping key
                group_key = tuple(
                    getattr(event, field, '') if hasattr(event, field) else event.details.get(field, '')
                    for field in rule['groupby']
                )

                bucket_key = (rule['name'], group_key)
                self.event_buckets[bucket_key][now].append(event)

                # Clean old events
                cutoff_time = now - timedelta(seconds=rule['window'])
                old_keys = [ts for ts in self.event_buckets[bucket_key].keys() if ts < cutoff_time]
                for old_key in old_keys:
                    del self.event_buckets[bucket_key][old_key]

                # Check threshold
                total_events = sum(
                    len(events) for events in self.event_buckets[bucket_key].values()
                )

                if total_events >= rule['threshold']:
                    # Create correlated event
                    correlated_event = SecurityEvent(
                        event_id=str(uuid.uuid4()),
                        event_type=rule['output_event'],
                        severity=SecuritySeverity.HIGH,
                        timestamp=now,
                        user_id=event.user_id,
                        ip_address=event.ip_address,
                        user_agent=event.user_agent,
                        request_path=event.request_path,
                        details={
                            'correlation_rule': rule['name'],
                            'correlated_events': total_events,
                            'time_window': rule['window'],
                            'original_events': [e.event_id for events in self.event_buckets[bucket_key].values() for e in events]
                        },
                        threat_score=8.0
                    )
                    correlated_events.append(correlated_event)

                    # Clear bucket after correlation
                    self.event_buckets[bucket_key].clear()

        return correlated_events

class SecurityAlerter:
    """Send security alerts via multiple channels"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.alert_cooldown = {}  # Prevent alert spam
        self.cooldown_period = 300  # 5 minutes

    async def send_alert(self, event: SecurityEvent):
        """Send security alert"""
        # Check cooldown
        alert_key = f"{event.event_type.value}_{event.ip_address}"
        now = time.time()

        if alert_key in self.alert_cooldown:
            if now - self.alert_cooldown[alert_key] < self.cooldown_period:
                logger.debug(f"Alert suppressed due to cooldown: {alert_key}")
                return

        self.alert_cooldown[alert_key] = now

        # Send alerts based on severity
        if event.severity in [SecuritySeverity.HIGH, SecuritySeverity.CRITICAL]:
            await self._send_immediate_alert(event)
        elif event.severity == SecuritySeverity.MEDIUM:
            await self._send_batch_alert(event)

    async def _send_immediate_alert(self, event: SecurityEvent):
        """Send immediate alert for high/critical events"""
        try:
            # Email alert
            if self.config.get('email_enabled', False):
                await self._send_email_alert(event)

            # Webhook alert
            if self.config.get('webhook_enabled', False):
                await self._send_webhook_alert(event)

            # SMS alert (for critical events)
            if event.severity == SecuritySeverity.CRITICAL and self.config.get('sms_enabled', False):
                await self._send_sms_alert(event)

            logger.info(f"Immediate alert sent for event {event.event_id}")

        except Exception as e:
            logger.error(f"Failed to send immediate alert: {e}")

    async def _send_email_alert(self, event: SecurityEvent):
        """Send email alert"""
        try:
            smtp_config = self.config.get('smtp', {})
            if not smtp_config:
                return

            # Create message
            msg = MIMEMultipart()
            msg['From'] = smtp_config['from_email']
            msg['To'] = ', '.join(smtp_config['to_emails'])
            msg['Subject'] = f"ARTIFACTOR Security Alert - {event.severity.value.upper()}"

            # Email body
            body = f"""
ARTIFACTOR Security Alert

Event Type: {event.event_type.value}
Severity: {event.severity.value.upper()}
Threat Score: {event.threat_score:.1f}/10.0
Timestamp: {event.timestamp.isoformat()}

Details:
- User ID: {event.user_id or 'N/A'}
- IP Address: {event.ip_address}
- Request Path: {event.request_path}
- User Agent: {event.user_agent}

Event Details:
{json.dumps(event.details, indent=2)}

Event ID: {event.event_id}

This is an automated security alert from ARTIFACTOR v3.0
"""

            msg.attach(MIMEText(body, 'plain'))

            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_config['server'], smtp_config['port'], context=context) as server:
                server.login(smtp_config['username'], smtp_config['password'])
                server.send_message(msg)

        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")

    async def _send_webhook_alert(self, event: SecurityEvent):
        """Send webhook alert"""
        try:
            webhook_url = self.config.get('webhook_url')
            if not webhook_url:
                return

            payload = {
                'alert_type': 'security_event',
                'event': event.to_dict(),
                'timestamp': datetime.utcnow().isoformat(),
                'source': 'ARTIFACTOR-v3'
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Webhook alert sent for event {event.event_id}")
                    else:
                        logger.error(f"Webhook alert failed with status {response.status}")

        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")

    async def _send_sms_alert(self, event: SecurityEvent):
        """Send SMS alert for critical events"""
        # Implementation would depend on SMS service provider
        logger.info(f"SMS alert would be sent for critical event {event.event_id}")

    async def _send_batch_alert(self, event: SecurityEvent):
        """Add event to batch alerts (sent periodically)"""
        # Implementation for batched alerts
        logger.info(f"Event {event.event_id} added to batch alerts")

class SecurityMonitor:
    """Main security monitoring system"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.threat_scorer = ThreatScorer()
        self.aggregator = SecurityEventAggregator()
        self.alerter = SecurityAlerter(config.get('alerting', {}))

        # Storage
        self.redis_client = None
        self.sqlite_db = None
        self.event_handlers: List[Callable] = []

        # Statistics
        self.stats = {
            'total_events': 0,
            'events_by_type': defaultdict(int),
            'events_by_severity': defaultdict(int),
            'alerts_sent': 0,
            'start_time': datetime.utcnow()
        }

        # Initialize storage
        self._init_storage()

    def _init_storage(self):
        """Initialize storage backends"""
        try:
            # Initialize Redis for real-time data
            redis_url = self.config.get('redis_url')
            if redis_url:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)

            # Initialize SQLite for persistent storage
            db_path = self.config.get('sqlite_path', 'security_events.db')
            self.sqlite_db = sqlite3.connect(db_path, check_same_thread=False)
            self._create_tables()

        except Exception as e:
            logger.error(f"Failed to initialize storage: {e}")

    def _create_tables(self):
        """Create SQLite tables"""
        cursor = self.sqlite_db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                user_id TEXT,
                ip_address TEXT NOT NULL,
                user_agent TEXT,
                request_path TEXT,
                details TEXT,
                threat_score REAL,
                mitigated BOOLEAN,
                mitigation_action TEXT
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp ON security_events(timestamp);
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_event_type ON security_events(event_type);
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_ip_address ON security_events(ip_address);
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_severity ON security_events(severity);
        ''')

        self.sqlite_db.commit()

    async def log_security_event(
        self,
        event_type: SecurityEventType,
        ip_address: str,
        user_agent: str = "",
        request_path: str = "",
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: Optional[SecuritySeverity] = None
    ) -> SecurityEvent:
        """Log a security event"""
        try:
            # Calculate threat score
            threat_score = self.threat_scorer.calculate_score(event_type, details or {})

            # Determine severity if not provided
            if severity is None:
                if threat_score >= 9.0:
                    severity = SecuritySeverity.CRITICAL
                elif threat_score >= 7.0:
                    severity = SecuritySeverity.HIGH
                elif threat_score >= 4.0:
                    severity = SecuritySeverity.MEDIUM
                else:
                    severity = SecuritySeverity.LOW

            # Create event
            event = SecurityEvent(
                event_id=str(uuid.uuid4()),
                event_type=event_type,
                severity=severity,
                timestamp=datetime.utcnow(),
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                request_path=request_path,
                details=details or {},
                threat_score=threat_score
            )

            # Store event
            await self._store_event(event)

            # Check for correlations
            correlated_events = self.aggregator.aggregate_event(event)
            for correlated_event in correlated_events:
                await self._store_event(correlated_event)
                await self.alerter.send_alert(correlated_event)

            # Send alert if needed
            await self.alerter.send_alert(event)

            # Update statistics
            self._update_stats(event)

            # Call event handlers
            for handler in self.event_handlers:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(f"Event handler failed: {e}")

            logger.info(f"Security event logged: {event.event_type.value} (Score: {event.threat_score:.1f})")
            return event

        except Exception as e:
            logger.error(f"Failed to log security event: {e}")
            raise

    async def _store_event(self, event: SecurityEvent):
        """Store event in storage backends"""
        try:
            # Store in Redis (for real-time queries)
            if self.redis_client:
                await self.redis_client.setex(
                    f"security_event:{event.event_id}",
                    3600,  # 1 hour TTL
                    json.dumps(event.to_dict())
                )

                # Add to time-series for analytics
                await self.redis_client.zadd(
                    "security_events_timeline",
                    {event.event_id: event.timestamp.timestamp()}
                )

            # Store in SQLite (for persistence)
            if self.sqlite_db:
                cursor = self.sqlite_db.cursor()
                cursor.execute('''
                    INSERT INTO security_events
                    (event_id, event_type, severity, timestamp, user_id, ip_address,
                     user_agent, request_path, details, threat_score, mitigated, mitigation_action)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event.event_id,
                    event.event_type.value,
                    event.severity.value,
                    event.timestamp.isoformat(),
                    event.user_id,
                    event.ip_address,
                    event.user_agent,
                    event.request_path,
                    json.dumps(event.details),
                    event.threat_score,
                    event.mitigated,
                    event.mitigation_action
                ))
                self.sqlite_db.commit()

        except Exception as e:
            logger.error(f"Failed to store security event: {e}")

    def _update_stats(self, event: SecurityEvent):
        """Update monitoring statistics"""
        self.stats['total_events'] += 1
        self.stats['events_by_type'][event.event_type.value] += 1
        self.stats['events_by_severity'][event.severity.value] += 1

    def add_event_handler(self, handler: Callable):
        """Add custom event handler"""
        self.event_handlers.append(handler)

    async def get_recent_events(self, limit: int = 100) -> List[SecurityEvent]:
        """Get recent security events"""
        try:
            if self.sqlite_db:
                cursor = self.sqlite_db.cursor()
                cursor.execute('''
                    SELECT * FROM security_events
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (limit,))

                events = []
                for row in cursor.fetchall():
                    event_data = {
                        'event_id': row[0],
                        'event_type': SecurityEventType(row[1]),
                        'severity': SecuritySeverity(row[2]),
                        'timestamp': datetime.fromisoformat(row[3]),
                        'user_id': row[4],
                        'ip_address': row[5],
                        'user_agent': row[6],
                        'request_path': row[7],
                        'details': json.loads(row[8]) if row[8] else {},
                        'threat_score': row[9],
                        'mitigated': bool(row[10]),
                        'mitigation_action': row[11]
                    }
                    events.append(SecurityEvent(**event_data))

                return events

        except Exception as e:
            logger.error(f"Failed to get recent events: {e}")
            return []

    def get_security_dashboard_data(self) -> Dict[str, Any]:
        """Get data for security dashboard"""
        return {
            'statistics': self.stats,
            'uptime': (datetime.utcnow() - self.stats['start_time']).total_seconds(),
            'threat_level': self._calculate_current_threat_level(),
            'recent_alerts': len([e for e in self.event_handlers if hasattr(e, 'recent_alerts')])
        }

    def _calculate_current_threat_level(self) -> str:
        """Calculate current overall threat level"""
        # Simple implementation - in production this would be more sophisticated
        recent_high_severity = self.stats['events_by_severity'].get('high', 0)
        recent_critical = self.stats['events_by_severity'].get('critical', 0)

        if recent_critical > 0:
            return "CRITICAL"
        elif recent_high_severity > 5:
            return "HIGH"
        elif recent_high_severity > 0:
            return "MEDIUM"
        else:
            return "LOW"

# Global security monitor instance
security_monitor = None

def initialize_security_monitor(config: Dict[str, Any]) -> SecurityMonitor:
    """Initialize global security monitor"""
    global security_monitor
    security_monitor = SecurityMonitor(config)
    return security_monitor

# Convenience functions for common security events
async def log_authentication_failed(ip_address: str, user_agent: str, username: str = ""):
    """Log failed authentication attempt"""
    if security_monitor:
        await security_monitor.log_security_event(
            SecurityEventType.AUTHENTICATION_FAILED,
            ip_address,
            user_agent,
            "/api/auth/login",
            details={'username': username}
        )

async def log_sql_injection_attempt(ip_address: str, user_agent: str, query: str, user_id: str = None):
    """Log SQL injection attempt"""
    if security_monitor:
        await security_monitor.log_security_event(
            SecurityEventType.SQL_INJECTION_ATTEMPT,
            ip_address,
            user_agent,
            details={'query_preview': query[:200], 'full_query_hash': hashlib.sha256(query.encode()).hexdigest()},
            user_id=user_id
        )

async def log_file_upload_virus(ip_address: str, user_agent: str, filename: str, virus_name: str, user_id: str = None):
    """Log virus detected in file upload"""
    if security_monitor:
        await security_monitor.log_security_event(
            SecurityEventType.FILE_UPLOAD_VIRUS,
            ip_address,
            user_agent,
            "/api/artifacts/upload",
            details={'filename': filename, 'virus_name': virus_name},
            user_id=user_id
        )

# Export
__all__ = [
    'SecurityMonitor', 'SecurityEvent', 'SecurityEventType', 'SecuritySeverity',
    'ThreatScorer', 'SecurityAlerter', 'initialize_security_monitor',
    'log_authentication_failed', 'log_sql_injection_attempt', 'log_file_upload_virus'
]