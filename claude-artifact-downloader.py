#!/usr/bin/env python3
"""
Claude.ai Artifact Downloader with Multiple Fallbacks
Comprehensive mechanism for downloading all artifacts from Claude.ai projects
with proper filetype detection, validation, and multiple fallback methods.
"""

import os
import re
import json
import time
import mimetypes
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse, urljoin
from dataclasses import dataclass
import hashlib
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class Artifact:
    """Represents a Claude.ai artifact with metadata"""
    id: str
    title: str
    content: str
    type: str
    language: Optional[str] = None
    original_url: Optional[str] = None
    filename: Optional[str] = None
    size: int = 0
    checksum: Optional[str] = None

class FileTypeDetector:
    """Advanced filetype detection and validation"""

    # Language to extension mapping
    LANGUAGE_EXTENSIONS = {
        'python': '.py',
        'javascript': '.js',
        'typescript': '.ts',
        'html': '.html',
        'css': '.css',
        'java': '.java',
        'cpp': '.cpp',
        'c': '.c',
        'rust': '.rs',
        'go': '.go',
        'php': '.php',
        'ruby': '.rb',
        'swift': '.swift',
        'kotlin': '.kt',
        'scala': '.scala',
        'bash': '.sh',
        'shell': '.sh',
        'sql': '.sql',
        'xml': '.xml',
        'json': '.json',
        'yaml': '.yml',
        'yml': '.yml',
        'markdown': '.md',
        'md': '.md',
        'txt': '.txt',
        'text': '.txt',
        'dockerfile': 'Dockerfile',
        'makefile': 'Makefile',
        'cmake': 'CMakeLists.txt'
    }

    # Content-based detection patterns
    CONTENT_PATTERNS = {
        '.py': [r'#!/usr/bin/env python', r'import\s+\w+', r'def\s+\w+\(', r'class\s+\w+\('],
        '.js': [r'function\s+\w+\(', r'const\s+\w+\s*=', r'let\s+\w+\s*=', r'npm'],
        '.html': [r'<!DOCTYPE\s+html', r'<html', r'<head>', r'<body>'],
        '.css': [r'[.\#]\w+\s*\{', r'@import', r'@media'],
        '.json': [r'^\s*[\{\[]', r'"\w+"\s*:'],
        '.xml': [r'<\?xml\s+version', r'<\w+[^>]*>'],
        '.sql': [r'SELECT\s+', r'INSERT\s+INTO', r'CREATE\s+TABLE', r'DROP\s+'],
        '.md': [r'^#+\s+', r'\*\*\w+\*\*', r'```'],
        '.yml': [r'^\w+:', r'^\s*-\s+\w+', r'version:\s*'],
        '.sh': [r'#!/bin/(ba)?sh', r'echo\s+', r'if\s*\[\s*'],
        '.dockerfile': [r'^FROM\s+', r'^RUN\s+', r'^COPY\s+', r'^WORKDIR\s+']
    }

    @classmethod
    def detect_extension(cls, content: str, language: Optional[str] = None, filename: Optional[str] = None) -> str:
        """Detect file extension using multiple methods"""

        # Method 1: Use provided language
        if language:
            lang_lower = language.lower()
            if lang_lower in cls.LANGUAGE_EXTENSIONS:
                return cls.LANGUAGE_EXTENSIONS[lang_lower]

        # Method 2: Use provided filename
        if filename:
            _, ext = os.path.splitext(filename.lower())
            if ext:
                return ext

        # Method 3: Content-based detection
        content_lower = content.lower().strip()

        # Check for specific patterns
        for ext, patterns in cls.CONTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, content_lower, re.MULTILINE | re.IGNORECASE):
                    return ext

        # Method 4: Fallback heuristics
        if content.startswith('#!/'):
            return '.sh'
        elif content.startswith('<?xml'):
            return '.xml'
        elif content.startswith('{') or content.startswith('['):
            return '.json'
        elif '<html' in content_lower or '<!doctype' in content_lower:
            return '.html'

        # Default fallback
        return '.txt'

    @classmethod
    def validate_content(cls, content: str, expected_ext: str) -> bool:
        """Validate that content matches expected file type"""
        if expected_ext not in cls.CONTENT_PATTERNS:
            return True  # Can't validate unknown types

        patterns = cls.CONTENT_PATTERNS[expected_ext]
        return any(re.search(pattern, content, re.MULTILINE | re.IGNORECASE) for pattern in patterns)

class ClaudeArtifactDownloader:
    """Main downloader class with multiple fallback mechanisms"""

    def __init__(self, output_dir: str = "./artifacts", create_structure: bool = True,
                 max_workers: int = 4, rate_limit: float = 1.0):
        self.output_dir = Path(output_dir)
        self.create_structure = create_structure
        self.max_workers = max_workers
        self.rate_limit = rate_limit
        self.session = requests.Session()
        self.artifacts: List[Artifact] = []

        # Setup output directory
        self.output_dir.mkdir(exist_ok=True)

        # Configure session with connection pooling and retries
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS"],
            backoff_factor=1
        )
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=20)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Configure session with headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Claude Code Framework v8.0) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

    def extract_artifacts_from_url(self, url: str) -> List[Artifact]:
        """Method 1: Extract artifacts directly from Claude.ai conversation URL"""
        try:
            # Validate URL format
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError(f"Invalid URL format: {url}")

            logger.info(f"Extracting artifacts from URL: {url}")

            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # Check content size limit
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB limit
                raise ValueError(f"Response too large: {content_length} bytes")

            # Parse conversation data (this would need to be adapted based on actual Claude.ai structure)
            artifacts = self._parse_conversation_page(response.text)

            logger.info(f"Found {len(artifacts)} artifacts via URL extraction")
            return artifacts

        except requests.exceptions.Timeout:
            logger.error(f"URL request timed out: {url}")
            return []
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error for URL {url}: {e}")
            return []
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error for URL {url}: {e}")
            return []
        except ValueError as e:
            logger.error(f"URL validation error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in URL extraction: {e}")
            return []

    def extract_artifacts_from_export(self, export_file: str) -> List[Artifact]:
        """Method 2: Extract artifacts from exported conversation data"""
        try:
            logger.info(f"Extracting artifacts from export file: {export_file}")

            with open(export_file, 'r', encoding='utf-8') as f:
                if export_file.endswith('.json'):
                    data = json.load(f)
                    artifacts = self._parse_json_export(data)
                else:
                    content = f.read()
                    artifacts = self._parse_text_export(content)

            logger.info(f"Found {len(artifacts)} artifacts via export file")
            return artifacts

        except Exception as e:
            logger.error(f"Export file extraction failed: {e}")
            return []

    def extract_artifacts_from_clipboard(self) -> List[Artifact]:
        """Method 3: Extract artifacts from clipboard content"""
        try:
            # Try multiple clipboard access methods
            clipboard_content = None

            # Method 3a: Use pyperclip
            try:
                import pyperclip
                clipboard_content = pyperclip.paste()
            except ImportError:
                pass

            # Method 3b: Use tkinter
            if not clipboard_content:
                try:
                    import tkinter as tk
                    root = tk.Tk()
                    root.withdraw()
                    clipboard_content = root.clipboard_get()
                    root.destroy()
                except:
                    pass

            # Method 3c: Use subprocess (Linux/macOS)
            if not clipboard_content:
                try:
                    import subprocess
                    result = subprocess.run(['xclip', '-selection', 'clipboard', '-o'],
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        clipboard_content = result.stdout
                except:
                    pass

            if clipboard_content:
                artifacts = self._parse_text_export(clipboard_content)
                logger.info(f"Found {len(artifacts)} artifacts via clipboard")
                return artifacts

        except Exception as e:
            logger.error(f"Clipboard extraction failed: {e}")

        return []

    def extract_artifacts_manual_input(self) -> List[Artifact]:
        """Method 4: Manual artifact input with interactive prompts"""
        artifacts = []

        print("\n=== Manual Artifact Input Mode ===")
        print("Enter artifacts one by one. Type 'done' when finished.")

        artifact_id = 1
        while True:
            print(f"\n--- Artifact {artifact_id} ---")

            title = input("Title (or 'done' to finish): ").strip()
            if title.lower() == 'done':
                break

            language = input("Language/Type (optional): ").strip() or None
            filename = input("Filename (optional): ").strip() or None

            print("Content (end with '###END###' on a new line):")
            content_lines = []
            while True:
                line = input()
                if line.strip() == '###END###':
                    break
                content_lines.append(line)

            content = '\n'.join(content_lines)

            if content.strip():
                artifact = Artifact(
                    id=f"manual_{artifact_id}",
                    title=title,
                    content=content,
                    type="code" if language else "text",
                    language=language,
                    filename=filename
                )
                artifacts.append(artifact)
                print(f"✓ Added artifact: {title}")
                artifact_id += 1
            else:
                print("✗ Empty content, skipping")

        logger.info(f"Collected {len(artifacts)} artifacts via manual input")
        return artifacts

    def download_all_with_fallbacks(self, **kwargs) -> Tuple[int, int]:
        """Download all artifacts using multiple fallback methods"""

        # Clear previous artifacts
        self.artifacts = []

        # Method 1: URL extraction
        if 'url' in kwargs:
            artifacts = self.extract_artifacts_from_url(kwargs['url'])
            self.artifacts.extend(artifacts)

        # Method 2: Export file
        if 'export_file' in kwargs and not self.artifacts:
            artifacts = self.extract_artifacts_from_export(kwargs['export_file'])
            self.artifacts.extend(artifacts)

        # Method 3: Clipboard
        if not self.artifacts and kwargs.get('try_clipboard', True):
            artifacts = self.extract_artifacts_from_clipboard()
            self.artifacts.extend(artifacts)

        # Method 4: Manual input
        if not self.artifacts and kwargs.get('allow_manual', True):
            artifacts = self.extract_artifacts_manual_input()
            self.artifacts.extend(artifacts)

        if not self.artifacts:
            logger.error("No artifacts found with any method")
            return 0, 0

        # Download all artifacts
        return self._download_artifacts(self.artifacts)

    def _download_artifacts(self, artifacts: List[Artifact]) -> Tuple[int, int]:
        """Download artifacts to files with proper naming"""

        successful = 0
        failed = 0

        for i, artifact in enumerate(artifacts, 1):
            try:
                logger.info(f"Processing artifact {i}/{len(artifacts)}: {artifact.title}")

                # Generate filename
                filename = self._generate_filename(artifact)
                filepath = self.output_dir / filename

                # Create subdirectories if needed
                if self.create_structure:
                    filepath.parent.mkdir(parents=True, exist_ok=True)

                # Validate content size and safety
                if len(artifact.content) > 10 * 1024 * 1024:  # 10MB limit
                    logger.warning(f"Content too large for {artifact.title}, truncating")
                    content_to_write = artifact.content[:10 * 1024 * 1024] + "\n[TRUNCATED - Content exceeded 10MB limit]"
                else:
                    content_to_write = artifact.content

                # Security: Check for suspicious content patterns
                if self._is_suspicious_content(content_to_write):
                    logger.warning(f"Suspicious content detected in {artifact.title}, marking as .suspicious")
                    filepath = filepath.with_suffix(filepath.suffix + '.suspicious')

                # Write content to file with proper error handling
                try:
                    with open(filepath, 'w', encoding='utf-8', errors='replace') as f:
                        f.write(content_to_write)
                except UnicodeEncodeError:
                    logger.warning(f"Encoding issues with {artifact.title}, saving as binary")
                    with open(filepath.with_suffix('.bin'), 'wb') as f:
                        f.write(content_to_write.encode('utf-8', errors='replace'))

                # Verify file was written correctly
                if filepath.exists() and filepath.stat().st_size > 0:
                    successful += 1
                    logger.info(f"✓ Saved: {filepath}")

                    # Generate checksum
                    artifact.checksum = self._calculate_checksum(filepath)
                    artifact.size = filepath.stat().st_size
                else:
                    failed += 1
                    logger.error(f"✗ Failed to save: {filepath}")

            except Exception as e:
                failed += 1
                logger.error(f"✗ Error processing {artifact.title}: {e}")

        # Generate manifest
        self._generate_manifest()

        return successful, failed

    def _generate_filename(self, artifact: Artifact) -> str:
        """Generate appropriate filename for artifact"""

        # Validate and sanitize title
        if not artifact.title or len(artifact.title.strip()) == 0:
            artifact.title = f"untitled_artifact_{artifact.id}"

        # Security: Prevent path traversal attacks
        title = artifact.title.replace('..', '').replace('/', '').replace('\\', '')

        # Clean title for filename - more restrictive for security
        clean_title = re.sub(r'[^\w\s.-]', '', title)
        clean_title = re.sub(r'[-\s]+', '_', clean_title).strip('_')

        # Limit filename length to prevent filesystem issues
        if len(clean_title) > 100:
            clean_title = clean_title[:100] + '_truncated'

        # Use provided filename if available
        if artifact.filename:
            base_name = Path(artifact.filename).stem
            provided_ext = Path(artifact.filename).suffix
        else:
            base_name = clean_title or f"artifact_{artifact.id}"
            provided_ext = None

        # Detect proper extension
        detected_ext = FileTypeDetector.detect_extension(
            artifact.content,
            artifact.language,
            artifact.filename
        )

        # Use provided extension if it matches content, otherwise use detected
        if provided_ext and FileTypeDetector.validate_content(artifact.content, provided_ext):
            extension = provided_ext
        else:
            extension = detected_ext

        # Handle special cases
        if extension == '.dockerfile' or base_name.lower() == 'dockerfile':
            return 'Dockerfile'
        elif extension == '.makefile' or base_name.lower() in ['makefile', 'cmake']:
            return 'Makefile' if 'make' in base_name.lower() else 'CMakeLists.txt'

        # Create final filename
        filename = f"{base_name}{extension}"

        # Create subdirectory structure if enabled
        if self.create_structure and artifact.language:
            return f"{artifact.language}/{filename}"

        return filename

    def _calculate_checksum(self, filepath: Path) -> str:
        """Calculate SHA256 checksum of file"""
        hash_sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def _generate_manifest(self):
        """Generate manifest file with artifact metadata"""
        manifest = {
            'download_info': {
                'timestamp': time.time(),
                'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_artifacts': len(self.artifacts),
                'output_directory': str(self.output_dir.absolute())
            },
            'artifacts': []
        }

        for artifact in self.artifacts:
            manifest['artifacts'].append({
                'id': artifact.id,
                'title': artifact.title,
                'type': artifact.type,
                'language': artifact.language,
                'filename': self._generate_filename(artifact),
                'size': artifact.size,
                'checksum': artifact.checksum
            })

        manifest_path = self.output_dir / 'manifest.json'
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        logger.info(f"Generated manifest: {manifest_path}")

    def _parse_conversation_page(self, html_content: str) -> List[Artifact]:
        """Parse Claude.ai conversation page HTML (placeholder)"""
        # This would need to be implemented based on actual Claude.ai page structure
        artifacts = []

        # Example pattern matching (would need real implementation)
        # artifact_pattern = r'<div class="artifact".*?</div>'
        # matches = re.findall(artifact_pattern, html_content, re.DOTALL)

        logger.warning("Conversation page parsing not implemented - would need Claude.ai page structure analysis")
        return artifacts

    def _parse_json_export(self, data: dict) -> List[Artifact]:
        """Parse JSON export data"""
        artifacts = []

        # Handle different possible JSON structures
        if 'artifacts' in data:
            for i, item in enumerate(data['artifacts']):
                artifact = Artifact(
                    id=item.get('id', f"json_{i}"),
                    title=item.get('title', f"Artifact {i+1}"),
                    content=item.get('content', ''),
                    type=item.get('type', 'text'),
                    language=item.get('language'),
                    filename=item.get('filename')
                )
                artifacts.append(artifact)

        elif 'messages' in data:
            # Parse conversation messages for code blocks
            artifacts.extend(self._extract_code_blocks_from_messages(data['messages']))

        return artifacts

    def _parse_text_export(self, content: str) -> List[Artifact]:
        """Parse text export or clipboard content"""
        artifacts = []

        # Method 1: Look for code blocks with language specifiers
        code_block_pattern = r'```(\w+)?\n(.*?)\n```'
        matches = re.findall(code_block_pattern, content, re.DOTALL)

        for i, (language, code) in enumerate(matches):
            if code.strip():
                artifact = Artifact(
                    id=f"codeblock_{i}",
                    title=f"Code Block {i+1}" + (f" ({language})" if language else ""),
                    content=code.strip(),
                    type="code",
                    language=language if language else None
                )
                artifacts.append(artifact)

        # Method 2: Look for artifact markers (if using specific format)
        artifact_pattern = r'=== ARTIFACT: (.+?) ===\n(.*?)(?=\n=== ARTIFACT:|$)'
        artifact_matches = re.findall(artifact_pattern, content, re.DOTALL)

        for title, artifact_content in artifact_matches:
            artifact = Artifact(
                id=f"marked_{len(artifacts)}",
                title=title.strip(),
                content=artifact_content.strip(),
                type="text"
            )
            artifacts.append(artifact)

        return artifacts

    def _extract_code_blocks_from_messages(self, messages: list) -> List[Artifact]:
        """Extract code blocks from conversation messages"""
        artifacts = []

        for msg_i, message in enumerate(messages):
            content = message.get('content', '')
            if isinstance(content, list):
                # Handle structured content
                for item in content:
                    if item.get('type') == 'text':
                        text_artifacts = self._parse_text_export(item.get('text', ''))
                        artifacts.extend(text_artifacts)
            elif isinstance(content, str):
                text_artifacts = self._parse_text_export(content)
                artifacts.extend(text_artifacts)

        return artifacts

    def _is_suspicious_content(self, content: str) -> bool:
        """Check for potentially suspicious or malicious content patterns"""

        # Define suspicious patterns
        suspicious_patterns = [
            r'eval\s*\(',  # Code evaluation
            r'exec\s*\(',  # Code execution
            r'import\s+subprocess',  # Subprocess execution
            r'import\s+os.*system',  # OS system calls
            r'__import__\s*\(',  # Dynamic imports
            r'base64\.decode',  # Base64 decoding (potential obfuscation)
            r'urllib\.request',  # Network requests in downloaded code
            r'socket\.socket',  # Raw socket operations
            r'pickle\.loads',  # Pickle deserialization (dangerous)
            r'marshal\.loads',  # Marshal deserialization
            r'compile\s*\(',  # Dynamic compilation
            r'globals\s*\(\)',  # Global namespace access
            r'locals\s*\(\)',  # Local namespace access
            r'\.system\s*\(',  # System command execution
            r'shell\s*=\s*True',  # Shell command injection risk
        ]

        # Check for suspicious patterns
        content_lower = content.lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, content_lower):
                logger.warning(f"Suspicious pattern detected: {pattern}")
                return True

        return False

    def close(self):
        """Clean up resources"""
        if hasattr(self, 'session'):
            self.session.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

def main():
    """Main CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description='Download Claude.ai artifacts with multiple fallbacks')
    parser.add_argument('--url', help='Claude.ai conversation URL')
    parser.add_argument('--export-file', help='Exported conversation file')
    parser.add_argument('--output-dir', default='./artifacts', help='Output directory')
    parser.add_argument('--no-structure', action='store_true', help='Disable directory structure creation')
    parser.add_argument('--no-clipboard', action='store_true', help='Skip clipboard check')
    parser.add_argument('--no-manual', action='store_true', help='Skip manual input')
    parser.add_argument('--verbose', action='store_true', help='Verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create downloader
    downloader = ClaudeArtifactDownloader(
        output_dir=args.output_dir,
        create_structure=not args.no_structure
    )

    # Download with fallbacks
    successful, failed = downloader.download_all_with_fallbacks(
        url=args.url,
        export_file=args.export_file,
        try_clipboard=not args.no_clipboard,
        allow_manual=not args.no_manual
    )

    # Report results
    print(f"\n=== Download Complete ===")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Output directory: {args.output_dir}")

    if successful > 0:
        print(f"Check manifest.json for detailed artifact information")

if __name__ == '__main__':
    main()