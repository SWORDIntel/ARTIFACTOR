"""
ARTIFACTOR v3.0 Secure File Handler
Comprehensive file upload security with virus scanning, content validation, and sandboxing
"""

import os
import asyncio
import logging
import hashlib
import mimetypes
import tempfile
import shutil
import subprocess
import magic
import re
from typing import Dict, List, Optional, Tuple, Any, Union, BinaryIO
from pathlib import Path
from datetime import datetime, timedelta
import uuid
import aiofiles
from PIL import Image
import zipfile
import tarfile
import json
import yaml
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import clamd  # ClamAV Python client
from fastapi import UploadFile, HTTPException, status

logger = logging.getLogger(__name__)

class FileSecurityError(Exception):
    """Raised when file security validation fails"""
    pass

class VirusScanError(Exception):
    """Raised when virus scanning fails"""
    pass

class FileValidator:
    """Comprehensive file validation and security checking"""

    def __init__(self):
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.max_total_files = 1000
        self.quarantine_dir = Path("quarantine")
        self.quarantine_dir.mkdir(exist_ok=True, mode=0o700)

        # Allowed MIME types (whitelist approach)
        self.allowed_mime_types = {
            # Text files
            'text/plain', 'text/markdown', 'text/csv', 'text/x-python', 'text/javascript',
            'text/css', 'text/html', 'text/xml', 'text/yaml',

            # Application files
            'application/json', 'application/yaml', 'application/xml',
            'application/pdf', 'application/zip',

            # Images (restricted)
            'image/png', 'image/jpeg', 'image/gif', 'image/svg+xml',

            # Code files
            'application/x-python-code', 'application/javascript',
        }

        # Dangerous file extensions (blacklist)
        self.dangerous_extensions = {
            # Executables
            '.exe', '.bat', '.cmd', '.com', '.scr', '.pif', '.msi', '.reg',
            '.app', '.deb', '.rpm', '.dmg', '.iso', '.img',

            # Scripts
            '.sh', '.bash', '.zsh', '.ps1', '.vbs', '.jar', '.class',

            # Security sensitive
            '.key', '.pem', '.p12', '.pfx', '.crt', '.cer',

            # Potentially dangerous documents
            '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',

            # Archives (potential zip bombs)
            '.rar', '.7z', '.tar', '.gz', '.bz2',

            # Database files
            '.db', '.sqlite', '.mdb',

            # System files
            '.dll', '.so', '.dylib', '.sys', '.drv'
        }

        # Dangerous content patterns
        self.dangerous_patterns = {
            'script_injection': re.compile(
                r'<script[^>]*>.*?</script>|javascript:|vbscript:|data:text/html|on\w+\s*=',
                re.IGNORECASE | re.DOTALL
            ),
            'sql_injection': re.compile(
                r'(\bUNION\s+SELECT\b|;\s*(DROP|DELETE|INSERT|UPDATE)\s+|\b1\s*=\s*1\b)',
                re.IGNORECASE
            ),
            'path_traversal': re.compile(
                r'(\.\.\/|\.\.\\|%2e%2e%2f|%252e%252e%252f)',
                re.IGNORECASE
            ),
            'command_injection': re.compile(
                r'(\|\s*\w+|;\s*\w+|`[^`]+`|\$\([^)]+\)|&\s*\w+)',
                re.IGNORECASE
            ),
            'php_code': re.compile(
                r'<\?php|<\?=|\beval\s*\(|\bsystem\s*\(|\bexec\s*\(',
                re.IGNORECASE
            ),
            'powershell': re.compile(
                r'powershell|invoke-expression|iex\s+|downloadstring',
                re.IGNORECASE
            )
        }

        # Initialize ClamAV if available
        self.clamav_available = self._init_clamav()

    def _init_clamav(self) -> bool:
        """Initialize ClamAV virus scanner"""
        try:
            self.clamd_client = clamd.ClamdUnixSocket()
            # Test connection
            self.clamd_client.ping()
            logger.info("ClamAV initialized successfully")
            return True
        except Exception as e:
            logger.warning(f"ClamAV not available: {e}")
            return False

    async def validate_file(
        self,
        file: Union[UploadFile, BinaryIO, bytes],
        filename: str,
        max_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """Comprehensive file validation"""
        validation_result = {
            'valid': False,
            'errors': [],
            'warnings': [],
            'file_info': {},
            'security_scan': {}
        }

        try:
            # Get file content
            if isinstance(file, UploadFile):
                content = await file.read()
                await file.seek(0)  # Reset for potential reuse
            elif isinstance(file, bytes):
                content = file
            else:
                content = file.read()

            # Basic file validation
            file_size = len(content)
            max_allowed = max_size or self.max_file_size

            # Size validation
            if file_size > max_allowed:
                validation_result['errors'].append(
                    f"File too large: {file_size} bytes > {max_allowed} bytes"
                )
                return validation_result

            if file_size == 0:
                validation_result['errors'].append("Empty file")
                return validation_result

            # File extension validation
            file_ext = Path(filename).suffix.lower()
            if file_ext in self.dangerous_extensions:
                validation_result['errors'].append(f"Dangerous file extension: {file_ext}")
                return validation_result

            # MIME type detection and validation
            mime_type = magic.from_buffer(content, mime=True)
            if mime_type not in self.allowed_mime_types:
                validation_result['errors'].append(f"Disallowed MIME type: {mime_type}")
                return validation_result

            # File info collection
            validation_result['file_info'] = {
                'filename': filename,
                'size': file_size,
                'mime_type': mime_type,
                'extension': file_ext,
                'sha256': hashlib.sha256(content).hexdigest(),
                'md5': hashlib.md5(content).hexdigest()
            }

            # Content validation
            content_validation = await self._validate_file_content(content, mime_type, filename)
            validation_result['errors'].extend(content_validation['errors'])
            validation_result['warnings'].extend(content_validation['warnings'])

            # Virus scanning
            if self.clamav_available:
                virus_scan = await self._scan_for_viruses(content, filename)
                validation_result['security_scan'].update(virus_scan)
                if not virus_scan['clean']:
                    validation_result['errors'].append("Virus detected")

            # Archive validation (if applicable)
            if mime_type in ['application/zip', 'application/x-tar']:
                archive_validation = await self._validate_archive(content, mime_type)
                validation_result['errors'].extend(archive_validation['errors'])
                validation_result['warnings'].extend(archive_validation['warnings'])

            # Image validation (if applicable)
            if mime_type.startswith('image/'):
                image_validation = await self._validate_image(content)
                validation_result['errors'].extend(image_validation['errors'])
                validation_result['warnings'].extend(image_validation['warnings'])

            # Final validation result
            validation_result['valid'] = len(validation_result['errors']) == 0

            return validation_result

        except Exception as e:
            logger.error(f"File validation error: {e}")
            validation_result['errors'].append(f"Validation error: {str(e)}")
            return validation_result

    async def _validate_file_content(
        self,
        content: bytes,
        mime_type: str,
        filename: str
    ) -> Dict[str, List[str]]:
        """Validate file content for security threats"""
        result = {'errors': [], 'warnings': []}

        try:
            # Decode content for text analysis
            if mime_type.startswith('text/') or mime_type in [
                'application/json', 'application/yaml', 'application/xml'
            ]:
                try:
                    text_content = content.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        text_content = content.decode('latin-1')
                    except UnicodeDecodeError:
                        result['warnings'].append("Could not decode file as text")
                        return result

                # Check for dangerous patterns
                for pattern_name, pattern in self.dangerous_patterns.items():
                    if pattern.search(text_content):
                        result['errors'].append(f"Dangerous {pattern_name} pattern detected")

                # Check for embedded binaries in text files
                if b'\x00' in content:
                    result['errors'].append("Null bytes detected in text file")

                # Check for extremely long lines (potential DoS)
                lines = text_content.split('\n')
                max_line_length = 10000
                long_lines = [i for i, line in enumerate(lines) if len(line) > max_line_length]
                if long_lines:
                    result['warnings'].append(f"Very long lines detected: {len(long_lines)} lines")

                # Check for excessive file complexity
                if len(lines) > 100000:
                    result['warnings'].append("File has excessive number of lines")

            # Binary file analysis
            else:
                # Check for embedded executables
                pe_signature = b'\x4d\x5a'  # PE executable signature
                elf_signature = b'\x7f\x45\x4c\x46'  # ELF executable signature

                if content.startswith(pe_signature) or content.startswith(elf_signature):
                    result['errors'].append("Embedded executable detected")

                # Check for suspicious binary patterns
                suspicious_strings = [
                    b'cmd.exe', b'powershell', b'system32', b'/bin/sh',
                    b'eval', b'exec', b'base64_decode'
                ]

                for suspicious in suspicious_strings:
                    if suspicious in content:
                        result['warnings'].append(f"Suspicious binary content: {suspicious.decode('ascii', errors='ignore')}")

        except Exception as e:
            logger.error(f"Content validation error: {e}")
            result['errors'].append(f"Content validation failed: {str(e)}")

        return result

    async def _scan_for_viruses(self, content: bytes, filename: str) -> Dict[str, Any]:
        """Scan file content for viruses using ClamAV"""
        result = {
            'clean': True,
            'threats': [],
            'scan_time': 0,
            'scanner': 'ClamAV'
        }

        if not self.clamav_available:
            result['scanner'] = 'Not Available'
            return result

        try:
            start_time = datetime.now()

            # Scan content
            scan_result = self.clamd_client.instream(content)

            scan_time = (datetime.now() - start_time).total_seconds()
            result['scan_time'] = scan_time

            # Parse results
            if scan_result['stream'][0] == 'FOUND':
                result['clean'] = False
                threat_name = scan_result['stream'][1]
                result['threats'].append(threat_name)
                logger.warning(f"Virus detected in {filename}: {threat_name}")

                # Quarantine the file
                await self._quarantine_file(content, filename, f"Virus: {threat_name}")

            elif scan_result['stream'][0] == 'ERROR':
                result['clean'] = False
                result['threats'].append('Scan error')
                logger.error(f"Virus scan error for {filename}")

        except Exception as e:
            logger.error(f"Virus scanning failed: {e}")
            result['clean'] = False
            result['threats'].append(f"Scan failed: {str(e)}")

        return result

    async def _validate_archive(self, content: bytes, mime_type: str) -> Dict[str, List[str]]:
        """Validate archive files for security threats"""
        result = {'errors': [], 'warnings': []}

        try:
            with tempfile.NamedTemporaryFile() as temp_file:
                temp_file.write(content)
                temp_file.flush()

                if mime_type == 'application/zip':
                    await self._validate_zip_archive(temp_file.name, result)
                elif mime_type == 'application/x-tar':
                    await self._validate_tar_archive(temp_file.name, result)

        except Exception as e:
            logger.error(f"Archive validation error: {e}")
            result['errors'].append(f"Archive validation failed: {str(e)}")

        return result

    async def _validate_zip_archive(self, file_path: str, result: Dict[str, List[str]]):
        """Validate ZIP archive for security issues"""
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                # Check for zip bombs
                total_size = 0
                file_count = 0

                for info in zip_file.infolist():
                    file_count += 1
                    total_size += info.file_size

                    # Check for excessive file count
                    if file_count > 1000:
                        result['errors'].append("Archive contains too many files (potential zip bomb)")
                        break

                    # Check for excessive uncompressed size
                    if total_size > 1024 * 1024 * 1024:  # 1GB
                        result['errors'].append("Archive uncompressed size too large (potential zip bomb)")
                        break

                    # Check for dangerous file paths
                    if '..' in info.filename or info.filename.startswith('/'):
                        result['errors'].append(f"Dangerous file path in archive: {info.filename}")

                    # Check compression ratio for zip bomb detection
                    if info.compress_size > 0:
                        ratio = info.file_size / info.compress_size
                        if ratio > 100:  # Suspicious compression ratio
                            result['warnings'].append(f"High compression ratio detected: {ratio:.1f}")

        except zipfile.BadZipFile:
            result['errors'].append("Corrupted ZIP archive")
        except Exception as e:
            result['errors'].append(f"ZIP validation error: {str(e)}")

    async def _validate_tar_archive(self, file_path: str, result: Dict[str, List[str]]):
        """Validate TAR archive for security issues"""
        try:
            with tarfile.open(file_path, 'r') as tar_file:
                total_size = 0
                file_count = 0

                for member in tar_file.getmembers():
                    file_count += 1
                    total_size += member.size

                    # Check limits
                    if file_count > 1000:
                        result['errors'].append("Archive contains too many files")
                        break

                    if total_size > 1024 * 1024 * 1024:  # 1GB
                        result['errors'].append("Archive uncompressed size too large")
                        break

                    # Check for dangerous paths
                    if member.name.startswith('/') or '..' in member.name:
                        result['errors'].append(f"Dangerous file path in archive: {member.name}")

                    # Check for symlink attacks
                    if member.issym() or member.islnk():
                        result['warnings'].append(f"Symbolic/hard link detected: {member.name}")

        except tarfile.TarError:
            result['errors'].append("Corrupted TAR archive")
        except Exception as e:
            result['errors'].append(f"TAR validation error: {str(e)}")

    async def _validate_image(self, content: bytes) -> Dict[str, List[str]]:
        """Validate image files for security threats"""
        result = {'errors': [], 'warnings': []}

        try:
            with tempfile.NamedTemporaryFile() as temp_file:
                temp_file.write(content)
                temp_file.flush()

                # Open and validate image
                with Image.open(temp_file.name) as img:
                    # Check image dimensions
                    width, height = img.size
                    max_dimension = 10000

                    if width > max_dimension or height > max_dimension:
                        result['errors'].append(f"Image dimensions too large: {width}x{height}")

                    # Check for potential decompression bombs
                    pixel_count = width * height
                    if pixel_count > 100_000_000:  # 100 megapixels
                        result['warnings'].append("Very large image (potential decompression bomb)")

                    # Check for suspicious metadata
                    if hasattr(img, '_getexif') and img._getexif():
                        exif_data = img._getexif()
                        if exif_data and len(str(exif_data)) > 10000:
                            result['warnings'].append("Excessive EXIF data detected")

        except Exception as e:
            result['errors'].append(f"Image validation error: {str(e)}")

        return result

    async def _quarantine_file(self, content: bytes, filename: str, reason: str):
        """Quarantine suspicious files"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            quarantine_filename = f"{timestamp}_{uuid.uuid4().hex[:8]}_{filename}"
            quarantine_path = self.quarantine_dir / quarantine_filename

            # Save file to quarantine
            async with aiofiles.open(quarantine_path, 'wb') as f:
                await f.write(content)

            # Create metadata file
            metadata = {
                'original_filename': filename,
                'quarantine_timestamp': timestamp,
                'reason': reason,
                'sha256': hashlib.sha256(content).hexdigest(),
                'size': len(content)
            }

            metadata_path = quarantine_path.with_suffix('.metadata.json')
            async with aiofiles.open(metadata_path, 'w') as f:
                await f.write(json.dumps(metadata, indent=2))

            logger.warning(f"File quarantined: {filename} -> {quarantine_filename} (Reason: {reason})")

        except Exception as e:
            logger.error(f"Failed to quarantine file {filename}: {e}")

class SecureFileUploadHandler:
    """Secure file upload handler with comprehensive protection"""

    def __init__(self):
        self.validator = FileValidator()
        self.upload_stats = {}
        self.blocked_hashes = set()

    async def handle_upload(
        self,
        file: UploadFile,
        user_id: str,
        upload_dir: str = "uploads",
        max_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """Handle file upload with comprehensive security"""
        upload_id = str(uuid.uuid4())
        upload_result = {
            'upload_id': upload_id,
            'success': False,
            'file_path': None,
            'file_info': {},
            'validation_result': {},
            'errors': []
        }

        try:
            # Initial validation
            if not file.filename:
                raise FileSecurityError("No filename provided")

            if len(file.filename) > 255:
                raise FileSecurityError("Filename too long")

            # Check user upload limits
            if not await self._check_user_limits(user_id):
                raise FileSecurityError("User upload limit exceeded")

            # Read file content
            content = await file.read()
            await file.seek(0)

            # Check for duplicate/blocked files
            file_hash = hashlib.sha256(content).hexdigest()
            if file_hash in self.blocked_hashes:
                raise FileSecurityError("File blocked due to previous security violations")

            # Comprehensive validation
            validation_result = await self.validator.validate_file(file, file.filename, max_size)
            upload_result['validation_result'] = validation_result

            if not validation_result['valid']:
                # Block file hash if serious security issues
                if any('virus' in error.lower() or 'malicious' in error.lower()
                      for error in validation_result['errors']):
                    self.blocked_hashes.add(file_hash)

                raise FileSecurityError(f"File validation failed: {'; '.join(validation_result['errors'])}")

            # Create secure upload directory
            upload_path = Path(upload_dir) / user_id
            upload_path.mkdir(parents=True, exist_ok=True, mode=0o750)

            # Generate secure filename
            secure_filename = self._generate_secure_filename(file.filename)
            file_path = upload_path / secure_filename

            # Ensure unique filename
            counter = 1
            while file_path.exists():
                name_parts = secure_filename.rsplit('.', 1)
                if len(name_parts) == 2:
                    new_name = f"{name_parts[0]}_{counter}.{name_parts[1]}"
                else:
                    new_name = f"{secure_filename}_{counter}"
                file_path = upload_path / new_name
                counter += 1

            # Save file securely
            await self._save_file_secure(content, file_path)

            # Update file info
            upload_result.update({
                'success': True,
                'file_path': str(file_path),
                'file_info': validation_result['file_info']
            })

            # Update upload statistics
            await self._update_upload_stats(user_id, len(content), True)

            logger.info(f"File uploaded successfully: {file.filename} -> {file_path}")
            return upload_result

        except Exception as e:
            logger.error(f"File upload failed: {e}")
            upload_result['errors'].append(str(e))
            await self._update_upload_stats(user_id, 0, False)
            return upload_result

    async def _check_user_limits(self, user_id: str) -> bool:
        """Check user upload limits"""
        try:
            # Get user upload statistics
            user_stats = self.upload_stats.get(user_id, {
                'total_files': 0,
                'total_size': 0,
                'uploads_today': 0,
                'last_upload': None
            })

            # Check daily limits
            today = datetime.now().date()
            if user_stats['last_upload']:
                last_upload_date = user_stats['last_upload'].date()
                if last_upload_date != today:
                    user_stats['uploads_today'] = 0

            # Apply limits
            max_files_per_user = 1000
            max_size_per_user = 5 * 1024 * 1024 * 1024  # 5GB
            max_uploads_per_day = 100

            if user_stats['total_files'] >= max_files_per_user:
                return False

            if user_stats['total_size'] >= max_size_per_user:
                return False

            if user_stats['uploads_today'] >= max_uploads_per_day:
                return False

            return True

        except Exception as e:
            logger.error(f"Error checking user limits: {e}")
            return False

    def _generate_secure_filename(self, original_filename: str) -> str:
        """Generate secure filename"""
        # Remove dangerous characters
        safe_chars = re.sub(r'[^a-zA-Z0-9._-]', '_', original_filename)

        # Limit length
        if len(safe_chars) > 100:
            name_parts = safe_chars.rsplit('.', 1)
            if len(name_parts) == 2:
                ext = name_parts[1][:10]  # Limit extension length
                name = name_parts[0][:90]  # Limit name length
                safe_chars = f"{name}.{ext}"
            else:
                safe_chars = safe_chars[:100]

        # Add timestamp prefix for uniqueness
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{timestamp}_{safe_chars}"

    async def _save_file_secure(self, content: bytes, file_path: Path):
        """Save file with secure permissions"""
        try:
            # Write file atomically
            temp_path = file_path.with_suffix(f"{file_path.suffix}.tmp")

            async with aiofiles.open(temp_path, 'wb') as f:
                await f.write(content)

            # Set secure permissions
            os.chmod(temp_path, 0o640)  # Owner read/write, group read

            # Atomic move
            temp_path.rename(file_path)

        except Exception as e:
            # Cleanup on failure
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)
            raise FileSecurityError(f"Failed to save file securely: {e}")

    async def _update_upload_stats(self, user_id: str, file_size: int, success: bool):
        """Update user upload statistics"""
        if user_id not in self.upload_stats:
            self.upload_stats[user_id] = {
                'total_files': 0,
                'total_size': 0,
                'uploads_today': 0,
                'successful_uploads': 0,
                'failed_uploads': 0,
                'last_upload': None
            }

        stats = self.upload_stats[user_id]
        stats['last_upload'] = datetime.now()

        if success:
            stats['total_files'] += 1
            stats['total_size'] += file_size
            stats['uploads_today'] += 1
            stats['successful_uploads'] += 1
        else:
            stats['failed_uploads'] += 1

    async def delete_file_secure(self, file_path: str, user_id: str) -> bool:
        """Securely delete file with verification"""
        try:
            path = Path(file_path)

            # Verify user owns the file
            if user_id not in str(path):
                raise FileSecurityError("Unauthorized file access")

            if not path.exists():
                return True

            # Secure deletion (overwrite before delete)
            if path.is_file():
                # Overwrite with random data
                file_size = path.stat().st_size
                with open(path, 'rb+') as f:
                    f.write(os.urandom(file_size))
                    f.flush()
                    os.fsync(f.fileno())

                # Delete file
                path.unlink()

            logger.info(f"File securely deleted: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Secure file deletion failed: {e}")
            return False

    def get_upload_statistics(self) -> Dict[str, Any]:
        """Get upload statistics and security metrics"""
        total_files = sum(stats['total_files'] for stats in self.upload_stats.values())
        total_size = sum(stats['total_size'] for stats in self.upload_stats.values())
        total_users = len(self.upload_stats)

        return {
            'total_files_uploaded': total_files,
            'total_size_uploaded': total_size,
            'total_users': total_users,
            'blocked_file_hashes': len(self.blocked_hashes),
            'quarantined_files': len(list(self.validator.quarantine_dir.glob('*'))),
            'user_statistics': self.upload_stats
        }

# Global secure file upload handler
secure_file_handler = SecureFileUploadHandler()

# Export
__all__ = [
    'SecureFileUploadHandler', 'FileValidator', 'FileSecurityError',
    'VirusScanError', 'secure_file_handler'
]