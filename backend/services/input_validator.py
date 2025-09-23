"""
ARTIFACTOR v3.0 Comprehensive Input Validator
Advanced input validation and sanitization with security focus
"""

import re
import html
import json
import logging
import unicodedata
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import uuid
import ipaddress
import email_validator
from pydantic import BaseModel, ValidationError, validator
import bleach
from urllib.parse import urlparse
import base64

logger = logging.getLogger(__name__)

class InputValidationError(Exception):
    """Raised when input validation fails"""
    pass

class SanitizationResult(BaseModel):
    """Result of input sanitization"""
    original: str
    sanitized: str
    threats_detected: List[str]
    safe: bool

class SecurityPattern:
    """Security patterns for threat detection"""

    def __init__(self):
        self.patterns = self._compile_patterns()

    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile security threat patterns"""
        return {
            'sql_injection': re.compile(
                r'''
                (?i)                                    # Case insensitive
                (
                    (\s|^|;)(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|DECLARE|GRANT|REVOKE)\s+
                    |(\s|^)(OR|AND)\s+\d+\s*=\s*\d+     # 1=1, 1=0 patterns
                    |(\s|^)(OR|AND)\s+['"]\w+['"]       # OR 'x'='x' patterns
                    |\-\-\s*.*$                         # SQL comments
                    |/\*.*?\*/                          # Block comments
                    |\bUNION\s+(ALL\s+)?SELECT\b        # UNION SELECT attacks
                    |\bCONCAT\s*\(.*,.*\)               # String concatenation
                    |\bCHAR\s*\(\d+\)                   # Character conversion
                    |\bCAST\s*\(.*\bAS\b                # Type casting
                    |\bCONVERT\s*\(.*,.*\)              # Convert function
                    |\bEXEC\s*\(                        # Dynamic execution
                    |\bSP_\w+                           # Stored procedures
                    |\bXP_\w+                           # Extended procedures
                    |\bDBMS_\w+                         # Oracle packages
                    |\bUTL_\w+                          # Oracle utilities
                    |\bSYS\.\w+                         # System objects
                    |\bINFORMATION_SCHEMA\b             # Schema information
                    |\bPG_\w+                           # PostgreSQL functions
                    |\bMYSQL\.\w+                       # MySQL specifics
                    |\bMASTER\.\.\w+                    # SQL Server master
                    |\bMSDB\.\.\w+                      # SQL Server msdb
                    |\bTEMPDB\.\.\w+                    # SQL Server tempdb
                )
                ''',
                re.VERBOSE | re.MULTILINE
            ),

            'xss': re.compile(
                r'''
                (?i)                                    # Case insensitive
                (
                    <script[^>]*>.*?</script>           # Script tags
                    |<iframe[^>]*>.*?</iframe>          # Iframe tags
                    |<object[^>]*>.*?</object>          # Object tags
                    |<embed[^>]*>.*?</embed>            # Embed tags
                    |<link[^>]*>                        # Link tags
                    |<meta[^>]*>                        # Meta tags
                    |<style[^>]*>.*?</style>            # Style tags
                    |<form[^>]*>.*?</form>              # Form tags
                    |<input[^>]*>                       # Input tags
                    |<button[^>]*>.*?</button>          # Button tags
                    |javascript:                        # JavaScript protocol
                    |vbscript:                          # VBScript protocol
                    |data:text/html                     # Data URLs with HTML
                    |data:application/                  # Data URLs with apps
                    |on\w+\s*=                          # Event handlers
                    |expression\s*\(                    # CSS expressions
                    |@import\s+                         # CSS imports
                    |document\.(write|writeln|domain|cookie|location)  # DOM manipulation
                    |window\.(open|location|eval)       # Window manipulation
                    |eval\s*\(                          # Eval function
                    |setTimeout\s*\(                    # Timer functions
                    |setInterval\s*\(                   # Interval functions
                    |alert\s*\(                         # Alert function
                    |confirm\s*\(                       # Confirm function
                    |prompt\s*\(                        # Prompt function
                    |String\.fromCharCode               # Character encoding
                    |unescape\s*\(                      # URL unescape
                    |decodeURI\s*\(                     # URI decoding
                    |atob\s*\(                          # Base64 decode
                    |btoa\s*\(                          # Base64 encode
                )
                ''',
                re.VERBOSE | re.DOTALL
            ),

            'command_injection': re.compile(
                r'''
                (?i)                                    # Case insensitive
                (
                    (\|\s*\w+|;\s*\w+|&&\s*\w+|\|\|\s*\w+)  # Command chaining
                    |`[^`]+`                            # Backticks
                    |\$\([^)]+\)                        # Command substitution
                    |&\s*\w+                            # Background execution
                    |\bnc\s+                            # Netcat
                    |\bnetcat\s+                        # Netcat
                    |\bcurl\s+                          # Curl
                    |\bwget\s+                          # Wget
                    |\bssh\s+                           # SSH
                    |\btelnet\s+                        # Telnet
                    |\bftp\s+                           # FTP
                    |\bping\s+                          # Ping
                    |\bnslookup\s+                      # DNS lookup
                    |\bdig\s+                           # DNS dig
                    |\bcat\s+/                          # File reading
                    |\bls\s+                            # Directory listing
                    |\bps\s+                            # Process listing
                    |\bkill\s+                          # Process killing
                    |\bchmod\s+                         # Permission change
                    |\bchown\s+                         # Ownership change
                    |\bmount\s+                         # Mount operations
                    |\bumount\s+                        # Unmount operations
                    |\bsu\s+                            # Switch user
                    |\bsudo\s+                          # Sudo execution
                    |\b/bin/\w+                         # Binary execution
                    |\b/usr/bin/\w+                     # Binary execution
                    |\b/sbin/\w+                        # System binaries
                    |\b/usr/sbin/\w+                    # System binaries
                    |\bpowersh\w*\s+                    # PowerShell
                    |\bcmd\s+                           # Windows command
                    |\bcmd\.exe                         # Windows command
                    |\bpowershell\s+                    # PowerShell
                    |\bInvoke-Expression                # PowerShell invoke
                    |\bStart-Process                    # PowerShell process start
                )
                ''',
                re.VERBOSE
            ),

            'path_traversal': re.compile(
                r'''
                (?i)                                    # Case insensitive
                (
                    (\.\./|\.\.\\)                      # Directory traversal
                    |(%2e%2e%2f|%2e%2e\\)               # URL encoded traversal
                    |(%252e%252e%252f|%252e%252e\\)     # Double URL encoded
                    |file://                            # File protocol
                    |/etc/passwd                        # System files
                    |/etc/shadow                        # Password file
                    |/etc/hosts                         # Hosts file
                    |/proc/                             # Process info
                    |/sys/                              # System info
                    |/dev/                              # Device files
                    |/var/log/                          # Log files
                    |/root/                             # Root directory
                    |/home/\w+/\.ssh/                   # SSH keys
                    |/home/\w+/\.aws/                   # AWS credentials
                    |/home/\w+/\.env                    # Environment files
                    |\.ssh/id_rsa                       # SSH private key
                    |\.ssh/authorized_keys              # SSH authorized keys
                    |\.aws/credentials                  # AWS credentials
                    |\.git/config                       # Git config
                    |web\.config                        # IIS config
                    |\.htaccess                         # Apache config
                    |WEB-INF/                           # Java web config
                    |META-INF/                          # Java metadata
                    |\.jar                              # Java archives
                    |\.war                              # Web archives
                    |\.class                            # Java class files
                    |boot\.ini                          # Windows boot
                    |win\.ini                           # Windows config
                    |system\.ini                        # Windows system
                    |c:\\windows\\                      # Windows system
                    |c:\\users\\                        # Windows users
                )
                ''',
                re.VERBOSE
            ),

            'ldap_injection': re.compile(
                r'''
                (?i)                                    # Case insensitive
                (
                    (\*|\(|\)|&|\||!|=|<|>|~|;)         # LDAP special chars
                    |\bou\s*=                           # Organizational unit
                    |\bcn\s*=                           # Common name
                    |\bdc\s*=                           # Domain component
                    |\buid\s*=                          # User ID
                    |\bsn\s*=                           # Surname
                    |\bobjectClass\s*=                  # Object class
                    |\bmemberOf\s*=                     # Group membership
                )
                ''',
                re.VERBOSE
            ),

            'xml_injection': re.compile(
                r'''
                (?i)                                    # Case insensitive
                (
                    <!DOCTYPE[^>]*>                     # DOCTYPE declaration
                    |<!ENTITY[^>]*>                     # Entity declaration
                    |&\w+;                              # Entity references
                    |&#\d+;                             # Numeric entities
                    |&#x[0-9a-f]+;                      # Hex entities
                    |<!\[CDATA\[                        # CDATA sections
                    |\]\]>                              # CDATA end
                )
                ''',
                re.VERBOSE | re.DOTALL
            ),

            'nosql_injection': re.compile(
                r'''
                (?i)                                    # Case insensitive
                (
                    \$where\s*:                         # MongoDB $where
                    |\$ne\s*:                           # MongoDB $ne
                    |\$gt\s*:                           # MongoDB $gt
                    |\$lt\s*:                           # MongoDB $lt
                    |\$regex\s*:                        # MongoDB $regex
                    |\$or\s*:                           # MongoDB $or
                    |\$and\s*:                          # MongoDB $and
                    |\$not\s*:                          # MongoDB $not
                    |\$in\s*:                           # MongoDB $in
                    |\$nin\s*:                          # MongoDB $nin
                    |\$exists\s*:                       # MongoDB $exists
                    |\$type\s*:                         # MongoDB $type
                    |\$expr\s*:                         # MongoDB $expr
                    |\$function\s*:                     # MongoDB function
                    |\$accumulator\s*:                  # MongoDB accumulator
                    |this\.\w+                          # JavaScript this
                    |eval\s*\(                          # JavaScript eval
                    |Function\s*\(                      # JavaScript Function
                )
                ''',
                re.VERBOSE
            ),

            'template_injection': re.compile(
                r'''
                (?i)                                    # Case insensitive
                (
                    \{\{.*?\}\}                         # Handlebars/Mustache
                    |\{%.*?%\}                          # Jinja2/Django
                    |\{#.*?#\}                          # Jinja2 comments
                    |\$\{.*?\}                          # JavaScript template
                    |<%.*?%>                            # JSP/ERB
                    |<%=.*?%>                           # JSP/ERB output
                    |<%#.*?%>                           # JSP/ERB comments
                    |#\{.*?\}                           # Ruby interpolation
                    |\[\[.*?\]\]                        # Go templates
                )
                ''',
                re.VERBOSE | re.DOTALL
            )
        }

class ComprehensiveInputValidator:
    """Comprehensive input validation and sanitization"""

    def __init__(self):
        self.security_patterns = SecurityPattern()
        self.max_length_limits = {
            'username': 50,
            'email': 255,
            'name': 100,
            'description': 1000,
            'content': 100000,
            'url': 2000,
            'filename': 255,
            'comment': 5000
        }

        # Allowed HTML tags for content sanitization
        self.allowed_html_tags = [
            'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'ul', 'ol', 'li', 'blockquote', 'code', 'pre'
        ]

        self.allowed_html_attributes = {
            '*': ['class', 'id'],
            'a': ['href', 'title'],
            'img': ['src', 'alt', 'title', 'width', 'height']
        }

    def validate_and_sanitize(
        self,
        data: Any,
        field_type: str,
        field_name: str = "field",
        max_length: Optional[int] = None,
        allow_html: bool = False,
        required: bool = True
    ) -> SanitizationResult:
        """Comprehensive validation and sanitization"""

        if data is None:
            if required:
                raise InputValidationError(f"{field_name} is required")
            return SanitizationResult(
                original="",
                sanitized="",
                threats_detected=[],
                safe=True
            )

        # Convert to string for processing
        original_data = str(data)
        threats_detected = []

        # Length validation
        max_len = max_length or self.max_length_limits.get(field_type, 1000)
        if len(original_data) > max_len:
            raise InputValidationError(f"{field_name} exceeds maximum length of {max_len}")

        # Unicode normalization
        normalized_data = unicodedata.normalize('NFKC', original_data)

        # Security threat detection
        threats_detected.extend(self._detect_threats(normalized_data))

        # Type-specific validation
        validated_data = self._validate_by_type(normalized_data, field_type, field_name)

        # Content sanitization
        if allow_html:
            sanitized_data = self._sanitize_html(validated_data)
        else:
            sanitized_data = self._sanitize_text(validated_data)

        # Final security check
        final_threats = self._detect_threats(sanitized_data)
        threats_detected.extend(final_threats)

        # Remove duplicates
        threats_detected = list(set(threats_detected))

        # Determine if input is safe
        is_safe = len(threats_detected) == 0

        # Log threats if detected
        if threats_detected:
            logger.warning(f"Security threats detected in {field_name}: {threats_detected}")

        return SanitizationResult(
            original=original_data,
            sanitized=sanitized_data,
            threats_detected=threats_detected,
            safe=is_safe
        )

    def _detect_threats(self, data: str) -> List[str]:
        """Detect security threats in input"""
        threats = []

        for threat_type, pattern in self.security_patterns.patterns.items():
            if pattern.search(data):
                threats.append(threat_type)

        # Additional threat detection
        if self._contains_suspicious_encoding(data):
            threats.append("suspicious_encoding")

        if self._contains_excessive_unicode(data):
            threats.append("excessive_unicode")

        if self._contains_binary_data(data):
            threats.append("binary_data")

        return threats

    def _validate_by_type(self, data: str, field_type: str, field_name: str) -> str:
        """Type-specific validation"""
        try:
            if field_type == 'email':
                return self._validate_email(data, field_name)
            elif field_type == 'url':
                return self._validate_url(data, field_name)
            elif field_type == 'username':
                return self._validate_username(data, field_name)
            elif field_type == 'filename':
                return self._validate_filename(data, field_name)
            elif field_type == 'uuid':
                return self._validate_uuid(data, field_name)
            elif field_type == 'ip_address':
                return self._validate_ip_address(data, field_name)
            elif field_type == 'json':
                return self._validate_json(data, field_name)
            elif field_type == 'base64':
                return self._validate_base64(data, field_name)
            elif field_type in ['content', 'description', 'comment']:
                return self._validate_text_content(data, field_name)
            else:
                return self._validate_generic_text(data, field_name)
        except Exception as e:
            raise InputValidationError(f"Validation failed for {field_name}: {str(e)}")

    def _validate_email(self, data: str, field_name: str) -> str:
        """Validate email address"""
        try:
            validated = email_validator.validate_email(data)
            return validated.email
        except email_validator.EmailNotValidError as e:
            raise InputValidationError(f"Invalid email format for {field_name}: {str(e)}")

    def _validate_url(self, data: str, field_name: str) -> str:
        """Validate URL"""
        try:
            parsed = urlparse(data)

            # Check scheme
            if parsed.scheme not in ['http', 'https', 'ftp', 'ftps']:
                raise InputValidationError(f"Invalid URL scheme for {field_name}")

            # Check for dangerous characters
            if any(char in data for char in ['<', '>', '"', '\'', '`']):
                raise InputValidationError(f"URL contains dangerous characters for {field_name}")

            # Check for local/private IPs in production
            if parsed.hostname:
                try:
                    ip = ipaddress.ip_address(parsed.hostname)
                    if ip.is_private or ip.is_loopback:
                        logger.warning(f"URL contains private/local IP for {field_name}")
                except ValueError:
                    pass  # Not an IP address

            return data
        except Exception as e:
            raise InputValidationError(f"Invalid URL format for {field_name}: {str(e)}")

    def _validate_username(self, data: str, field_name: str) -> str:
        """Validate username"""
        # Username pattern: alphanumeric, underscore, hyphen, period
        pattern = re.compile(r'^[a-zA-Z0-9._-]+$')

        if not pattern.match(data):
            raise InputValidationError(f"Username contains invalid characters for {field_name}")

        if len(data) < 3:
            raise InputValidationError(f"Username too short for {field_name}")

        if data.startswith('.') or data.endswith('.'):
            raise InputValidationError(f"Username cannot start or end with period for {field_name}")

        # Check for reserved usernames
        reserved = ['admin', 'root', 'system', 'api', 'www', 'mail', 'ftp']
        if data.lower() in reserved:
            raise InputValidationError(f"Username is reserved for {field_name}")

        return data

    def _validate_filename(self, data: str, field_name: str) -> str:
        """Validate filename"""
        # Remove path components
        filename = Path(data).name

        # Check for dangerous characters
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '/', '\\', '\x00']
        if any(char in filename for char in dangerous_chars):
            raise InputValidationError(f"Filename contains dangerous characters for {field_name}")

        # Check for reserved names (Windows)
        reserved_names = [
            'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5',
            'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4',
            'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        ]

        name_without_ext = Path(filename).stem.upper()
        if name_without_ext in reserved_names:
            raise InputValidationError(f"Filename is reserved for {field_name}")

        # Check for hidden files (starting with dot)
        if filename.startswith('.') and len(filename) > 1:
            logger.warning(f"Hidden file detected for {field_name}")

        return filename

    def _validate_uuid(self, data: str, field_name: str) -> str:
        """Validate UUID"""
        try:
            uuid_obj = uuid.UUID(data)
            return str(uuid_obj)
        except ValueError:
            raise InputValidationError(f"Invalid UUID format for {field_name}")

    def _validate_ip_address(self, data: str, field_name: str) -> str:
        """Validate IP address"""
        try:
            ip = ipaddress.ip_address(data)
            return str(ip)
        except ValueError:
            raise InputValidationError(f"Invalid IP address format for {field_name}")

    def _validate_json(self, data: str, field_name: str) -> str:
        """Validate JSON"""
        try:
            parsed = json.loads(data)

            # Check for deeply nested structures
            if self._get_json_depth(parsed) > 20:
                raise InputValidationError(f"JSON too deeply nested for {field_name}")

            # Check for excessive size
            if len(json.dumps(parsed)) > 100000:
                raise InputValidationError(f"JSON too large for {field_name}")

            return json.dumps(parsed, separators=(',', ':'))
        except json.JSONDecodeError as e:
            raise InputValidationError(f"Invalid JSON format for {field_name}: {str(e)}")

    def _validate_base64(self, data: str, field_name: str) -> str:
        """Validate Base64"""
        try:
            # Check if valid base64
            decoded = base64.b64decode(data, validate=True)

            # Check for reasonable size
            if len(decoded) > 10 * 1024 * 1024:  # 10MB
                raise InputValidationError(f"Base64 data too large for {field_name}")

            return data
        except Exception:
            raise InputValidationError(f"Invalid Base64 format for {field_name}")

    def _validate_text_content(self, data: str, field_name: str) -> str:
        """Validate text content"""
        # Check for excessive repetition
        if self._has_excessive_repetition(data):
            logger.warning(f"Excessive repetition detected in {field_name}")

        # Check for suspicious patterns
        if self._has_suspicious_patterns(data):
            logger.warning(f"Suspicious patterns detected in {field_name}")

        return data

    def _validate_generic_text(self, data: str, field_name: str) -> str:
        """Generic text validation"""
        # Check for control characters
        if any(ord(char) < 32 and char not in ['\n', '\r', '\t'] for char in data):
            raise InputValidationError(f"Text contains control characters for {field_name}")

        return data

    def _sanitize_html(self, data: str) -> str:
        """Sanitize HTML content"""
        return bleach.clean(
            data,
            tags=self.allowed_html_tags,
            attributes=self.allowed_html_attributes,
            strip=True,
            strip_comments=True
        )

    def _sanitize_text(self, data: str) -> str:
        """Sanitize plain text"""
        # HTML escape
        sanitized = html.escape(data, quote=True)

        # Remove null bytes
        sanitized = sanitized.replace('\x00', '')

        # Normalize whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized)

        # Strip leading/trailing whitespace
        sanitized = sanitized.strip()

        return sanitized

    def _contains_suspicious_encoding(self, data: str) -> bool:
        """Check for suspicious encoding patterns"""
        # URL encoding patterns
        url_encoded = re.search(r'%[0-9a-fA-F]{2}', data)
        if url_encoded and data.count('%') > 5:
            return True

        # Unicode escape patterns
        unicode_escaped = re.search(r'\\u[0-9a-fA-F]{4}', data)
        if unicode_escaped and data.count('\\u') > 3:
            return True

        # HTML entity patterns
        html_entities = re.search(r'&[a-zA-Z]+;', data)
        if html_entities and data.count('&') > 5:
            return True

        return False

    def _contains_excessive_unicode(self, data: str) -> bool:
        """Check for excessive Unicode characters"""
        unicode_count = sum(1 for char in data if ord(char) > 127)
        return unicode_count > len(data) * 0.5  # More than 50% non-ASCII

    def _contains_binary_data(self, data: str) -> bool:
        """Check for binary data patterns"""
        # Check for null bytes
        if '\x00' in data:
            return True

        # Check for excessive non-printable characters
        non_printable = sum(1 for char in data if not char.isprintable() and char not in ['\n', '\r', '\t'])
        return non_printable > len(data) * 0.1  # More than 10% non-printable

    def _get_json_depth(self, obj: Any, depth: int = 0) -> int:
        """Get maximum depth of JSON object"""
        if depth > 50:  # Prevent infinite recursion
            return depth

        if isinstance(obj, dict):
            return max([self._get_json_depth(value, depth + 1) for value in obj.values()], default=depth)
        elif isinstance(obj, list):
            return max([self._get_json_depth(item, depth + 1) for item in obj], default=depth)
        else:
            return depth

    def _has_excessive_repetition(self, data: str) -> bool:
        """Check for excessive character/pattern repetition"""
        # Check for repeated characters
        for char in set(data):
            if data.count(char) > len(data) * 0.3:  # More than 30% same character
                return True

        # Check for repeated substrings
        for i in range(2, min(10, len(data) // 3)):
            substring_counts = {}
            for j in range(len(data) - i + 1):
                substring = data[j:j+i]
                substring_counts[substring] = substring_counts.get(substring, 0) + 1

            for count in substring_counts.values():
                if count > 5:  # Same substring repeated more than 5 times
                    return True

        return False

    def _has_suspicious_patterns(self, data: str) -> bool:
        """Check for suspicious content patterns"""
        suspicious_patterns = [
            r'(.)\1{10,}',  # Same character repeated 10+ times
            r'[0-9]{50,}',  # Long numeric sequences
            r'[a-zA-Z]{100,}',  # Very long alphabetic sequences
            r'(\w+)\s+\1\s+\1',  # Same word repeated multiple times
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, data):
                return True

        return False

    def validate_batch(
        self,
        data_batch: Dict[str, Any],
        validation_rules: Dict[str, Dict[str, Any]]
    ) -> Dict[str, SanitizationResult]:
        """Validate multiple fields at once"""
        results = {}

        for field_name, field_value in data_batch.items():
            if field_name in validation_rules:
                rules = validation_rules[field_name]
                try:
                    result = self.validate_and_sanitize(
                        field_value,
                        rules.get('type', 'text'),
                        field_name,
                        rules.get('max_length'),
                        rules.get('allow_html', False),
                        rules.get('required', True)
                    )
                    results[field_name] = result
                except InputValidationError as e:
                    results[field_name] = SanitizationResult(
                        original=str(field_value) if field_value is not None else "",
                        sanitized="",
                        threats_detected=[str(e)],
                        safe=False
                    )

        return results

# Global validator instance
input_validator = ComprehensiveInputValidator()

# Common validation rule sets
VALIDATION_RULES = {
    'user_registration': {
        'username': {'type': 'username', 'max_length': 50, 'required': True},
        'email': {'type': 'email', 'max_length': 255, 'required': True},
        'full_name': {'type': 'text', 'max_length': 100, 'required': True},
        'password': {'type': 'text', 'max_length': 200, 'required': True}
    },
    'artifact_creation': {
        'title': {'type': 'text', 'max_length': 255, 'required': True},
        'description': {'type': 'description', 'max_length': 1000, 'required': False, 'allow_html': True},
        'content': {'type': 'content', 'max_length': 100000, 'required': True},
        'file_type': {'type': 'text', 'max_length': 50, 'required': True},
        'language': {'type': 'text', 'max_length': 50, 'required': False}
    },
    'comment_creation': {
        'content': {'type': 'comment', 'max_length': 5000, 'required': True, 'allow_html': True}
    },
    'plugin_manifest': {
        'name': {'type': 'text', 'max_length': 50, 'required': True},
        'version': {'type': 'text', 'max_length': 20, 'required': True},
        'description': {'type': 'description', 'max_length': 500, 'required': True},
        'author': {'type': 'text', 'max_length': 100, 'required': True},
        'entry_point': {'type': 'filename', 'max_length': 255, 'required': True}
    }
}

# Export
__all__ = [
    'ComprehensiveInputValidator', 'InputValidationError', 'SanitizationResult',
    'SecurityPattern', 'input_validator', 'VALIDATION_RULES'
]