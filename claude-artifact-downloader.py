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
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Set, Any
from urllib.parse import urlparse, urljoin
from dataclasses import dataclass, field
import hashlib
import logging
from collections import Counter, defaultdict
import pickle
from enum import Enum
import threading

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RegexPatternCache:
    """Thread-safe cache for compiled regex patterns to improve performance"""

    def __init__(self, max_size: int = 100):
        self._cache: Dict[str, re.Pattern] = {}
        self._max_size = max_size
        self._lock = threading.RLock()
        self._access_count: Dict[str, int] = {}

    def get_pattern(self, pattern: str, flags: int = 0) -> re.Pattern:
        """Get compiled regex pattern from cache or compile and cache it

        Args:
            pattern: Regex pattern string
            flags: Regex compilation flags

        Returns:
            Compiled regex pattern object
        """
        cache_key = f"{pattern}:{flags}"

        with self._lock:
            if cache_key in self._cache:
                self._access_count[cache_key] += 1
                return self._cache[cache_key]

            # Compile new pattern
            try:
                compiled_pattern = re.compile(pattern, flags)

                # Manage cache size
                if len(self._cache) >= self._max_size:
                    # Remove least accessed pattern
                    lru_key = min(self._access_count.keys(), key=self._access_count.get)
                    del self._cache[lru_key]
                    del self._access_count[lru_key]

                self._cache[cache_key] = compiled_pattern
                self._access_count[cache_key] = 1
                return compiled_pattern

            except re.error as e:
                logger.warning(f"Invalid regex pattern '{pattern}': {e}")
                # Return a pattern that matches nothing as fallback
                return re.compile(r'(?!.*)')

    def clear(self):
        """Clear the pattern cache"""
        with self._lock:
            self._cache.clear()
            self._access_count.clear()

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics for monitoring"""
        with self._lock:
            return {
                'cache_size': len(self._cache),
                'max_size': self._max_size,
                'total_accesses': sum(self._access_count.values())
            }

# Global pattern cache instance
regex_cache = RegexPatternCache()

# Custom Exception Classes for Better Error Handling
class ArtifactorException(Exception):
    """Base exception class for ARTIFACTOR-specific errors"""
    pass

class ConversationParsingError(ArtifactorException):
    """Raised when conversation data cannot be parsed"""
    def __init__(self, message: str, url: Optional[str] = None):
        super().__init__(message)
        self.url = url

class ArtifactDownloadError(ArtifactorException):
    """Raised when artifact download fails"""
    def __init__(self, message: str, artifact_id: Optional[str] = None):
        super().__init__(message)
        self.artifact_id = artifact_id

class FileTypeDetectionError(ArtifactorException):
    """Raised when file type detection fails critically"""
    pass

class EnvironmentSetupError(ArtifactorException):
    """Raised when environment setup fails"""
    pass

class ValidationError(ArtifactorException):
    """Raised when artifact validation fails"""
    def __init__(self, message: str, artifact_id: Optional[str] = None, validation_type: str = "general"):
        super().__init__(message)
        self.artifact_id = artifact_id
        self.validation_type = validation_type

class ProjectType(Enum):
    """Enumeration of detected project types"""
    WEB_APP = "web_app"
    API_BACKEND = "api_backend"
    DESKTOP_APP = "desktop_app"
    MOBILE_APP = "mobile_app"
    CLI_TOOL = "cli_tool"
    LIBRARY = "library"
    DOCUMENTATION = "documentation"
    CONFIGURATION = "configuration"
    MIXED = "mixed"
    UNKNOWN = "unknown"

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
    project_category: Optional[str] = None
    confidence_score: float = 0.0
    detected_patterns: List[str] = field(default_factory=list)

class MLFileTypeDetector:
    """ML-enhanced filetype detection and project analysis"""

    def __init__(self):
        self.content_patterns_db = {}
        self.project_patterns = {}
        self.user_corrections = []
        self.confidence_threshold = 0.7
        self._load_training_data()

    def _load_training_data(self):
        """Load or initialize training data for ML classification"""
        try:
            with open('filetype_training.pkl', 'rb') as f:
                training_data = pickle.load(f)
                self.content_patterns_db = training_data.get('patterns', {})
                self.user_corrections = training_data.get('corrections', [])
        except FileNotFoundError:
            # Initialize with basic patterns if no training data exists
            self._initialize_default_patterns()

    def _save_training_data(self):
        """Save training data for future use"""
        training_data = {
            'patterns': self.content_patterns_db,
            'corrections': self.user_corrections
        }
        with open('filetype_training.pkl', 'wb') as f:
            pickle.dump(training_data, f)

    def _initialize_default_patterns(self):
        """Initialize default patterns for project and file detection"""
        self.project_patterns = {
            ProjectType.WEB_APP: {
                'indicators': ['react', 'vue', 'angular', 'html', 'css', 'js', 'frontend'],
                'file_patterns': ['.html', '.css', '.js', '.jsx', '.vue', '.tsx'],
                'content_keywords': ['component', 'render', 'dom', 'browser', 'client-side']
            },
            ProjectType.API_BACKEND: {
                'indicators': ['api', 'server', 'backend', 'rest', 'graphql', 'endpoint'],
                'file_patterns': ['.py', '.js', '.java', '.go', '.rb'],
                'content_keywords': ['router', 'controller', 'middleware', 'database', 'auth']
            },
            ProjectType.DESKTOP_APP: {
                'indicators': ['desktop', 'gui', 'tkinter', 'qt', 'electron', 'native'],
                'file_patterns': ['.py', '.cpp', '.java', '.cs'],
                'content_keywords': ['window', 'button', 'dialog', 'gui', 'interface']
            },
            ProjectType.MOBILE_APP: {
                'indicators': ['mobile', 'ios', 'android', 'react-native', 'flutter'],
                'file_patterns': ['.swift', '.kt', '.java', '.dart', '.jsx'],
                'content_keywords': ['navigation', 'screen', 'mobile', 'device']
            },
            ProjectType.CLI_TOOL: {
                'indicators': ['cli', 'command', 'terminal', 'script', 'tool'],
                'file_patterns': ['.py', '.sh', '.js', '.go'],
                'content_keywords': ['argparse', 'click', 'sys.argv', 'main()']
            },
            ProjectType.LIBRARY: {
                'indicators': ['library', 'package', 'module', 'utility', 'helper'],
                'file_patterns': ['.py', '.js', '.java', '.cpp'],
                'content_keywords': ['export', 'import', 'class', 'function']
            }
        }

class FileTypeDetector:
    """Advanced filetype detection and validation"""

    # CONSTRUCTOR-Enhanced Language to extension mapping
    LANGUAGE_EXTENSIONS = {
        # Core Languages
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
        'cmake': 'CMakeLists.txt',

        # CONSTRUCTOR Enhancement: Modern Frameworks
        'jsx': '.jsx',
        'tsx': '.tsx',
        'vue': '.vue',
        'svelte': '.svelte',
        'react': '.jsx',
        'react-typescript': '.tsx',
        'angular': '.ts',
        'nextjs': '.tsx',
        'nuxt': '.vue',

        # CONSTRUCTOR Enhancement: Contemporary Languages
        'dart': '.dart',
        'flutter': '.dart',
        'zig': '.zig',
        'nim': '.nim',
        'crystal': '.cr',
        'elixir': '.ex',
        'erlang': '.erl',
        'haskell': '.hs',
        'clojure': '.clj',
        'fsharp': '.fs',
        'ocaml': '.ml',
        'reason': '.re',
        'purescript': '.purs',
        'elm': '.elm',
        'julia': '.jl',
        'r': '.r',
        'matlab': '.m',
        'lua': '.lua',
        'perl': '.pl',
        'raku': '.raku',
        'fortran': '.f90',
        'cobol': '.cob',
        'pascal': '.pas',
        'ada': '.adb',
        'assembly': '.asm',
        'nasm': '.asm',

        # CONSTRUCTOR Enhancement: Configuration & DevOps
        'toml': '.toml',
        'ini': '.ini',
        'conf': '.conf',
        'cfg': '.cfg',
        'terraform': '.tf',
        'ansible': '.yml',
        'kubernetes': '.yaml',
        'k8s': '.yaml',
        'helm': '.yaml',
        'prometheus': '.yml',
        'grafana': '.json',
        'jenkins': 'Jenkinsfile',
        'gitlab': '.gitlab-ci.yml',
        'github': '.yml',
        'circleci': '.yml',
        'travis': '.travis.yml',
        'appveyor': '.yml',

        # CONSTRUCTOR Enhancement: Data & Schema
        'csv': '.csv',
        'tsv': '.tsv',
        'parquet': '.parquet',
        'avro': '.avsc',
        'protobuf': '.proto',
        'graphql': '.graphql',
        'gql': '.gql',
        'prisma': '.prisma',
        'mongoose': '.js',
        'sequelize': '.js',

        # CONSTRUCTOR Enhancement: Specialized
        'sass': '.sass',
        'scss': '.scss',
        'less': '.less',
        'stylus': '.styl',
        'postcss': '.pcss',
        'tailwind': '.css',
        'latex': '.tex',
        'bibtex': '.bib',
        'jupyter': '.ipynb',
        'mathematica': '.nb',
        'verilog': '.v',
        'vhdl': '.vhd',
        'systemverilog': '.sv',
        'tcl': '.tcl',
        'expect': '.exp',
        'awk': '.awk',
        'sed': '.sed',
        'powershell': '.ps1',
        'batch': '.bat',
        'vim': '.vim',
        'emacs': '.el',
        'unity': '.cs',
        'unreal': '.cpp',
        'godot': '.gd',
        'solidity': '.sol',
        'vyper': '.vy',
        'cairo': '.cairo',
        'move': '.move',
    }

    # CONSTRUCTOR-Enhanced Content-based detection patterns
    CONTENT_PATTERNS = {
        # Core Languages - Enhanced
        '.py': [r'#!/usr/bin/env python', r'import\s+\w+', r'def\s+\w+\(', r'class\s+\w+\(', r'from\s+\w+\s+import', r'if\s+__name__\s*==\s*["\']__main__["\']', r'@\w+', r'async\s+def', r'await\s+', r'yield\s+', r'lambda\s+', r'with\s+\w+', r'try:', r'except\s+\w*:', r'finally:', r'raise\s+', r'assert\s+', r'print\s*\(', r'len\s*\(', r'range\s*\(', r'enumerate\s*\(', r'zip\s*\('],
        '.js': [r'function\s+\w+\(', r'const\s+\w+\s*=', r'let\s+\w+\s*=', r'npm', r'module\.exports', r'require\(', r'console\.log'],
        '.ts': [r'interface\s+\w+', r'type\s+\w+\s*=', r'import\s+.*from', r'export\s+', r':\s*\w+\s*[=;]', r'<.*>'],
        '.html': [r'<!DOCTYPE\s+html', r'<html', r'<head>', r'<body>', r'<div', r'<script', r'<style'],
        '.css': [r'[.\#]\w+\s*\{', r'@import', r'@media', r'@keyframes', r':\s*\w+;', r'background-color'],
        '.json': [r'^\s*[\{\[]', r'"\w+"\s*:', r':\s*".*"', r':\s*\d+', r':\s*true|false|null'],
        '.xml': [r'<\?xml\s+version', r'<\w+[^>]*>', r'</\w+>', r'xmlns:', r'<!\[CDATA\['],
        '.sql': [r'SELECT\s+', r'INSERT\s+INTO', r'CREATE\s+TABLE', r'DROP\s+', r'UPDATE\s+', r'DELETE\s+FROM', r'WHERE\s+'],
        '.md': [r'^#+\s+', r'\*\*\w+\*\*', r'```', r'\[.*\]\(.*\)', r'^\*\s+', r'^\d+\.\s+', r'!\[.*\]\(.*\)', r'`\w+`', r'^\|\s*\w+\s*\|', r'^>\s+', r'^\s*-\s+', r'^\s*\+\s+', r'---', r'\*\*\*', r'~~\w+~~', r'^```\w*$', r'^\s*```\s*$', r'<details>', r'<summary>', r'\[x\]', r'\[ \]'],
        '.yml': [r'^\w+:', r'^\s*-\s+\w+', r'version:\s*', r'name:\s*', r'spec:\s*', r'metadata:'],
        '.yaml': [r'^\w+:', r'^\s*-\s+\w+', r'version:\s*', r'name:\s*', r'spec:\s*', r'metadata:'],
        '.sh': [r'#!/bin/(ba)?sh', r'echo\s+', r'if\s*\[\s*', r'for\s+\w+\s+in', r'while\s+\[', r'function\s+\w+'],
        '.dockerfile': [r'^FROM\s+', r'^RUN\s+', r'^COPY\s+', r'^WORKDIR\s+', r'^ENV\s+', r'^EXPOSE\s+', r'^CMD\s+'],

        # CONSTRUCTOR Enhancement: Modern Frameworks
        '.jsx': [r'import\s+React', r'from\s+["\']react["\']', r'export\s+default', r'<\w+.*>', r'className=', r'onClick=', r'useState', r'useEffect'],
        '.tsx': [r'import\s+React', r'from\s+["\']react["\']', r'interface\s+\w+Props', r'type\s+\w+Props', r'<\w+.*>', r':\s*React\.', r'FC<'],
        '.vue': [r'<template>', r'<script>', r'<style.*scoped>', r'export\s+default\s*\{', r'Vue\.component', r'props:\s*\{', r'data\(\)\s*\{'],
        '.svelte': [r'<script>', r'<style>', r'export\s+let', r'import\s+', r'\$:', r'on:click', r'bind:'],

        # CONSTRUCTOR Enhancement: Contemporary Languages
        '.dart': [r'import\s+["\']dart:', r'void\s+main\(\)', r'class\s+\w+', r'final\s+', r'var\s+', r'String\s+', r'int\s+', r'double\s+'],
        '.zig': [r'const\s+std\s*=', r'pub\s+fn', r'var\s+', r'try\s+', r'if\s*\(', r'while\s*\(', r'for\s*\('],
        '.nim': [r'import\s+', r'proc\s+\w+', r'var\s+', r'let\s+', r'const\s+', r'type\s+', r'echo\s+'],
        '.cr': [r'require\s+', r'class\s+\w+', r'def\s+\w+', r'module\s+\w+', r'include\s+', r'extend\s+'],
        '.ex': [r'defmodule\s+\w+', r'def\s+\w+', r'defp\s+\w+', r'use\s+', r'import\s+', r'alias\s+', r'@spec'],
        '.rs': [r'fn\s+\w+', r'use\s+', r'mod\s+', r'pub\s+', r'struct\s+\w+', r'enum\s+\w+', r'impl\s+', r'let\s+mut', r'extern\s+crate', r'unsafe\s*\{', r'match\s+\w+', r'&mut\s+', r'Box<', r'Vec<', r'Option<', r'Result<'],
        '.go': [r'package\s+\w+', r'import\s+', r'func\s+\w+', r'var\s+', r'type\s+\w+', r'struct\s*\{', r'interface\s*\{'],

        # Enhanced C/C++ Detection
        '.c': [r'#include\s*<', r'#include\s*"', r'int\s+main\s*\(', r'printf\s*\(', r'scanf\s*\(', r'malloc\s*\(', r'free\s*\(', r'struct\s+\w+', r'typedef\s+', r'void\s+\w+\s*\(', r'return\s+\d+;', r'#define\s+'],
        '.cpp': [r'#include\s*<', r'#include\s*"', r'int\s+main\s*\(', r'std::', r'cout\s*<<', r'cin\s*>>', r'class\s+\w+', r'namespace\s+\w+', r'template\s*<', r'public:', r'private:', r'protected:', r'virtual\s+', r'override\s*;?$', r'new\s+\w+', r'delete\s+'],
        '.cc': [r'#include\s*<', r'#include\s*"', r'int\s+main\s*\(', r'std::', r'cout\s*<<', r'cin\s*>>', r'class\s+\w+', r'namespace\s+\w+', r'template\s*<', r'public:', r'private:', r'protected:'],
        '.cxx': [r'#include\s*<', r'#include\s*"', r'int\s+main\s*\(', r'std::', r'cout\s*<<', r'cin\s*>>', r'class\s+\w+', r'namespace\s+\w+', r'template\s*<', r'public:', r'private:', r'protected:'],
        '.h': [r'#ifndef\s+', r'#define\s+', r'#endif', r'#include\s*[<"]', r'extern\s+"C"', r'typedef\s+', r'struct\s+\w+', r'#pragma\s+once', r'void\s+\w+\s*\(', r'int\s+\w+\s*\('],
        '.hpp': [r'#ifndef\s+', r'#define\s+', r'#endif', r'#include\s*[<"]', r'class\s+\w+', r'namespace\s+\w+', r'template\s*<', r'#pragma\s+once', r'inline\s+', r'constexpr\s+'],

        # Enhanced Makefile Detection
        'Makefile': [r'^[A-Za-z_][A-Za-z0-9_]*\s*:', r'^\t', r'\$\([A-Z_]+\)', r'\.PHONY:', r'CC\s*=', r'CXX\s*=', r'CFLAGS\s*=', r'LDFLAGS\s*=', r'@echo', r'\$@', r'\$<', r'\$\^', r'clean:', r'install:', r'all:'],
        'makefile': [r'^[A-Za-z_][A-Za-z0-9_]*\s*:', r'^\t', r'\$\([A-Z_]+\)', r'\.PHONY:', r'CC\s*=', r'CXX\s*=', r'CFLAGS\s*=', r'LDFLAGS\s*=', r'@echo', r'\$@', r'\$<', r'\$\^'],
        'GNUmakefile': [r'^[A-Za-z_][A-Za-z0-9_]*\s*:', r'^\t', r'\$\([A-Z_]+\)', r'\.PHONY:', r'CC\s*=', r'CXX\s*=', r'CFLAGS\s*=', r'LDFLAGS\s*='],
        '.hs': [r'module\s+\w+', r'import\s+', r'where', r'data\s+\w+', r'type\s+\w+', r'class\s+\w+', r'instance\s+'],
        '.clj': [r'\(ns\s+', r'\(def\s+', r'\(defn\s+', r'\(let\s+', r'\(if\s+', r'\(cond\s+', r'\(require\s+'],
        '.jl': [r'using\s+', r'import\s+', r'function\s+\w+', r'end\s*$', r'module\s+\w+', r'struct\s+\w+'],

        # CONSTRUCTOR Enhancement: Configuration & DevOps
        '.toml': [r'^\[.*\]', r'^\w+\s*=', r'version\s*=', r'name\s*=', r'description\s*='],
        '.ini': [r'^\[.*\]', r'^\w+\s*=', r'#.*', r';.*'],
        '.conf': [r'^\w+\s+', r'#.*', r'=', r'server\s*\{', r'location\s+'],
        '.tf': [r'resource\s+', r'variable\s+', r'output\s+', r'provider\s+', r'data\s+', r'locals\s*\{'],
        '.proto': [r'syntax\s*=', r'package\s+', r'message\s+\w+', r'service\s+\w+', r'rpc\s+\w+', r'import\s+'],
        '.graphql': [r'type\s+\w+', r'query\s+', r'mutation\s+', r'subscription\s+', r'schema\s*\{', r'scalar\s+'],
        '.prisma': [r'generator\s+', r'datasource\s+', r'model\s+\w+', r'@id', r'@unique', r'@relation'],

        # CONSTRUCTOR Enhancement: DevOps CI/CD
        'Jenkinsfile': [r'pipeline\s*\{', r'agent\s+', r'stages\s*\{', r'stage\s*\(', r'steps\s*\{', r'sh\s+'],
        '.gitlab-ci.yml': [r'stages:', r'before_script:', r'script:', r'image:', r'variables:', r'cache:'],
        '.github/workflows/*.yml': [r'on:', r'jobs:', r'runs-on:', r'steps:', r'uses:', r'run:'],

        # CONSTRUCTOR Enhancement: Styling
        '.scss': [r'@import', r'@mixin', r'@include', r'@extend', r'\$\w+:', r'&:'],
        '.sass': [r'@import', r'@mixin', r'@include', r'@extend', r'\$\w+:', r'&'],
        '.less': [r'@import', r'@\w+:', r'&:', r'\.mixin', r'#\w+'],
        '.styl': [r'@import', r'@require', r'\$\w+', r'&', r'\.'],

        # CONSTRUCTOR Enhancement: Data Formats
        '.csv': [r'^.*,.*$', r'^\w+,\w+', r'".*",".*"'],
        '.tsv': [r'^.*\t.*$', r'^\w+\t\w+'],

        # CONSTRUCTOR Enhancement: Specialized
        '.tex': [r'\\documentclass', r'\\begin\{', r'\\end\{', r'\\usepackage', r'\\section', r'\\title'],
        '.ipynb': [r'"cells":', r'"metadata":', r'"nbformat":', r'"source":', r'"cell_type":'],
        '.ps1': [r'param\s*\(', r'Write-Host', r'Get-\w+', r'Set-\w+', r'\$\w+', r'if\s*\('],
        '.bat': [r'@echo', r'set\s+\w+', r'if\s+', r'goto\s+', r'call\s+', r'pause'],
        '.sol': [r'pragma\s+solidity', r'contract\s+\w+', r'function\s+\w+', r'modifier\s+\w+', r'mapping\s*\(', r'uint\d*'],
        '.gd': [r'extends\s+', r'class_name\s+', r'func\s+\w+', r'var\s+\w+', r'signal\s+\w+', r'onready\s+'],
    }

    @classmethod
    def detect_extension(cls, content: str, language: Optional[str] = None, filename: Optional[str] = None) -> Tuple[str, float]:
        """Detect file extension using multiple methods with confidence scoring"""

        confidence = 0.0
        detected_ext = '.txt'  # default fallback

        # Method 1: Use provided language (high confidence)
        if language:
            lang_lower = language.lower()
            if lang_lower in cls.LANGUAGE_EXTENSIONS:
                detected_ext = cls.LANGUAGE_EXTENSIONS[lang_lower]
                confidence = 0.9
                return detected_ext, confidence

        # Method 2: Use provided filename (medium-high confidence)
        if filename:
            _, ext = os.path.splitext(filename.lower())
            if ext:
                detected_ext = ext
                confidence = 0.8
                return detected_ext, confidence

        # Method 3: Content-based detection with scoring
        content_lower = content.lower().strip()
        pattern_scores = defaultdict(list)

        # Check for specific patterns and score them
        for ext, patterns in cls.CONTENT_PATTERNS.items():
            for pattern in patterns:
                if regex_cache.get_pattern(pattern, re.MULTILINE | re.IGNORECASE).search(content_lower):
                    pattern_scores[ext].append(0.7)  # base pattern match score

        # Find best scoring extension
        if pattern_scores:
            best_ext = max(pattern_scores.keys(), key=lambda x: sum(pattern_scores[x]))
            confidence = min(0.95, sum(pattern_scores[best_ext]) / len(pattern_scores[best_ext]))
            detected_ext = best_ext

        # Method 4: Fallback heuristics with confidence
        if confidence < 0.5:  # Only if no good match found
            if content.startswith('#!/'):
                detected_ext = '.sh'
                confidence = 0.6
            elif content.startswith('<?xml'):
                detected_ext = '.xml'
                confidence = 0.8
            elif content.startswith('{') or content.startswith('['):
                detected_ext = '.json'
                confidence = 0.7
            elif '<html' in content_lower or '<!doctype' in content_lower:
                detected_ext = '.html'
                confidence = 0.8
            else:
                detected_ext = '.txt'
                confidence = 0.3

        return detected_ext, confidence

    @classmethod
    def validate_content(cls, content: str, expected_ext: str) -> bool:
        """Validate that content matches expected file type"""
        if expected_ext not in cls.CONTENT_PATTERNS:
            return True  # Can't validate unknown types

        patterns = cls.CONTENT_PATTERNS[expected_ext]
        return any(regex_cache.get_pattern(pattern, re.MULTILINE | re.IGNORECASE).search(content) for pattern in patterns)

    @classmethod
    def analyze_project_structure(cls, artifacts: List[tuple]) -> dict:
        """CONSTRUCTOR-Enhanced: Analyze project structure and provide intelligent organization"""

        project_analysis = {
            'detected_frameworks': set(),
            'detected_languages': set(),
            'project_type': 'unknown',
            'suggested_structure': {},
            'confidence': 0.0,
            'recommendations': []
        }

        # Analyze each artifact
        for filename, content, detected_ext in artifacts:
            # Language detection
            for lang, ext in cls.LANGUAGE_EXTENSIONS.items():
                if detected_ext == ext:
                    project_analysis['detected_languages'].add(lang)

            # Framework detection
            content_lower = content.lower()

            # React/Next.js detection
            if any(pattern in content_lower for pattern in ['import react', 'from "react"', 'usestate', 'useeffect']):
                project_analysis['detected_frameworks'].add('react')
                if 'next' in content_lower or 'getserversideprops' in content_lower:
                    project_analysis['detected_frameworks'].add('nextjs')

            # Vue/Nuxt detection
            if any(pattern in content_lower for pattern in ['<template>', 'vue.component', 'export default {', '@nuxt']):
                project_analysis['detected_frameworks'].add('vue')
                if 'nuxt' in content_lower:
                    project_analysis['detected_frameworks'].add('nuxt')

            # Angular detection
            if any(pattern in content_lower for pattern in ['@component', '@injectable', '@ngmodule', 'angular']):
                project_analysis['detected_frameworks'].add('angular')

            # Backend framework detection
            if any(pattern in content_lower for pattern in ['express', 'app.get', 'app.post', 'require("express")']):
                project_analysis['detected_frameworks'].add('express')
            if any(pattern in content_lower for pattern in ['fastapi', 'from fastapi', '@app.get', 'uvicorn']):
                project_analysis['detected_frameworks'].add('fastapi')
            if any(pattern in content_lower for pattern in ['django', 'from django', 'models.model', 'urls.py']):
                project_analysis['detected_frameworks'].add('django')
            if any(pattern in content_lower for pattern in ['flask', 'from flask', '@app.route', 'render_template']):
                project_analysis['detected_frameworks'].add('flask')

            # Mobile framework detection
            if any(pattern in content_lower for pattern in ['flutter', 'dart', 'widget', 'statefulwidget']):
                project_analysis['detected_frameworks'].add('flutter')
            if any(pattern in content_lower for pattern in ['react native', 'react-native', 'expo']):
                project_analysis['detected_frameworks'].add('react-native')

            # DevOps detection
            if any(pattern in content_lower for pattern in ['dockerfile', 'from ', 'run ', 'copy ']):
                project_analysis['detected_frameworks'].add('docker')
            if any(pattern in content_lower for pattern in ['terraform', 'resource "', 'provider "', 'variable "']):
                project_analysis['detected_frameworks'].add('terraform')
            if any(pattern in content_lower for pattern in ['apiversion:', 'kind:', 'metadata:', 'spec:']):
                project_analysis['detected_frameworks'].add('kubernetes')

        # Determine project type based on detected frameworks and languages
        frameworks = project_analysis['detected_frameworks']
        languages = project_analysis['detected_languages']

        if 'react' in frameworks or 'vue' in frameworks or 'angular' in frameworks:
            if 'fastapi' in frameworks or 'express' in frameworks or 'django' in frameworks:
                project_analysis['project_type'] = 'fullstack_web_app'
                project_analysis['confidence'] = 0.9
            else:
                project_analysis['project_type'] = 'frontend_app'
                project_analysis['confidence'] = 0.8
        elif 'fastapi' in frameworks or 'express' in frameworks or 'django' in frameworks or 'flask' in frameworks:
            project_analysis['project_type'] = 'backend_api'
            project_analysis['confidence'] = 0.8
        elif 'flutter' in frameworks or 'react-native' in frameworks:
            project_analysis['project_type'] = 'mobile_app'
            project_analysis['confidence'] = 0.9
        elif 'docker' in frameworks or 'terraform' in frameworks or 'kubernetes' in frameworks:
            project_analysis['project_type'] = 'devops_infrastructure'
            project_analysis['confidence'] = 0.8
        elif 'python' in languages and len(languages) == 1:
            project_analysis['project_type'] = 'python_script'
            project_analysis['confidence'] = 0.6
        elif 'javascript' in languages or 'typescript' in languages:
            project_analysis['project_type'] = 'javascript_project'
            project_analysis['confidence'] = 0.6

        # Generate intelligent folder structure recommendations
        project_analysis['suggested_structure'] = cls._generate_folder_structure(
            project_analysis['project_type'],
            frameworks,
            languages
        )

        # Generate recommendations
        project_analysis['recommendations'] = cls._generate_recommendations(
            project_analysis['project_type'],
            frameworks,
            languages
        )

        return project_analysis

    @classmethod
    def _generate_folder_structure(cls, project_type: str, frameworks: set, languages: set) -> dict:
        """Generate intelligent folder structure based on project analysis"""

        structure = {}

        if project_type == 'fullstack_web_app':
            structure = {
                'frontend/': 'Client-side application files',
                'frontend/src/': 'Source code',
                'frontend/src/components/': 'Reusable UI components',
                'frontend/src/pages/': 'Page components',
                'frontend/src/utils/': 'Utility functions',
                'backend/': 'Server-side application',
                'backend/src/': 'Backend source code',
                'backend/api/': 'API endpoints',
                'backend/models/': 'Data models',
                'backend/services/': 'Business logic',
                'shared/': 'Shared types and utilities',
                'docs/': 'Documentation',
                'scripts/': 'Build and deployment scripts'
            }
        elif project_type == 'frontend_app':
            if 'react' in frameworks:
                structure = {
                    'src/': 'Source code',
                    'src/components/': 'React components',
                    'src/hooks/': 'Custom React hooks',
                    'src/utils/': 'Utility functions',
                    'src/styles/': 'CSS and styling',
                    'public/': 'Static assets',
                    'tests/': 'Test files'
                }
            elif 'vue' in frameworks:
                structure = {
                    'src/': 'Source code',
                    'src/components/': 'Vue components',
                    'src/views/': 'Page views',
                    'src/router/': 'Vue Router configuration',
                    'src/store/': 'Vuex store',
                    'src/assets/': 'Static assets',
                    'tests/': 'Test files'
                }
        elif project_type == 'backend_api':
            if 'fastapi' in frameworks:
                structure = {
                    'app/': 'Application code',
                    'app/api/': 'API endpoints',
                    'app/core/': 'Core configuration',
                    'app/models/': 'Database models',
                    'app/schemas/': 'Pydantic schemas',
                    'app/services/': 'Business logic',
                    'tests/': 'Test files',
                    'docs/': 'API documentation'
                }
            elif 'express' in frameworks:
                structure = {
                    'src/': 'Source code',
                    'src/routes/': 'Express routes',
                    'src/models/': 'Data models',
                    'src/middleware/': 'Express middleware',
                    'src/controllers/': 'Route controllers',
                    'src/utils/': 'Utility functions',
                    'tests/': 'Test files'
                }
        elif project_type == 'mobile_app':
            if 'flutter' in frameworks:
                structure = {
                    'lib/': 'Dart source code',
                    'lib/screens/': 'App screens',
                    'lib/widgets/': 'Custom widgets',
                    'lib/models/': 'Data models',
                    'lib/services/': 'API and business logic',
                    'lib/utils/': 'Utility functions',
                    'assets/': 'Images and static files',
                    'test/': 'Test files'
                }
        elif project_type == 'devops_infrastructure':
            structure = {
                'terraform/': 'Infrastructure as code',
                'docker/': 'Container configurations',
                'kubernetes/': 'K8s manifests',
                'scripts/': 'Automation scripts',
                'docs/': 'Infrastructure documentation',
                'monitoring/': 'Monitoring configurations'
            }
        else:
            # Generic structure
            structure = {
                'src/': 'Source code files',
                'docs/': 'Documentation',
                'tests/': 'Test files',
                'scripts/': 'Utility scripts',
                'config/': 'Configuration files'
            }

        return structure

    @classmethod
    def _generate_recommendations(cls, project_type: str, frameworks: set, languages: set) -> List[str]:
        """Generate intelligent recommendations based on project analysis"""

        recommendations = []

        # Framework-specific recommendations
        if 'react' in frameworks:
            recommendations.extend([
                "Consider organizing components by feature rather than type",
                "Use TypeScript for better type safety",
                "Implement proper state management (Redux/Context)",
                "Add ESLint and Prettier for code consistency"
            ])

        if 'fastapi' in frameworks:
            recommendations.extend([
                "Use Pydantic for request/response validation",
                "Implement proper error handling with HTTPException",
                "Add API documentation with OpenAPI",
                "Consider async/await for database operations"
            ])

        if 'docker' in frameworks:
            recommendations.extend([
                "Use multi-stage builds for smaller images",
                "Implement proper security scanning",
                "Use .dockerignore for smaller build context",
                "Consider using Alpine Linux for base images"
            ])

        # Language-specific recommendations
        if 'python' in languages:
            recommendations.extend([
                "Use virtual environments for dependency isolation",
                "Add type hints for better code documentation",
                "Implement proper logging with the logging module",
                "Use Black for code formatting"
            ])

        if 'typescript' in languages:
            recommendations.extend([
                "Configure strict TypeScript settings",
                "Use proper interface definitions",
                "Implement generic types where appropriate",
                "Consider using utility types"
            ])

        # Project type recommendations
        if project_type == 'fullstack_web_app':
            recommendations.extend([
                "Implement proper API versioning",
                "Use environment variables for configuration",
                "Set up proper CI/CD pipeline",
                "Implement comprehensive testing strategy"
            ])

        return recommendations

class ConversationAnalyzer:
    """Analyze entire Claude.ai conversations for enhanced project context and file relationships"""

    @staticmethod
    def analyze_conversation_intent(messages: List[Dict[str, Any]]) -> Dict[str, Union[str, List[str], float]]:
        """Determine overall project intent from conversation flow"""
        intent_analysis = {
            'project_type': 'unknown',
            'complexity_level': 'simple',
            'primary_frameworks': [],
            'user_goals': [],
            'development_phase': 'initial',
            'confidence': 0.0
        }

        if not messages:
            return intent_analysis

        # Analyze user messages for intent keywords
        user_messages = [msg.get('content', '') for msg in messages if msg.get('role') == 'user']
        all_content = ' '.join(user_messages).lower()

        # Project type detection from user requests
        if any(keyword in all_content for keyword in ['website', 'web app', 'frontend', 'react', 'vue', 'angular']):
            intent_analysis['project_type'] = 'web_application'
            intent_analysis['confidence'] += 0.3
        elif any(keyword in all_content for keyword in ['api', 'backend', 'server', 'fastapi', 'flask', 'express']):
            intent_analysis['project_type'] = 'backend_api'
            intent_analysis['confidence'] += 0.3
        elif any(keyword in all_content for keyword in ['mobile app', 'flutter', 'react native', 'ios', 'android']):
            intent_analysis['project_type'] = 'mobile_application'
            intent_analysis['confidence'] += 0.3
        elif any(keyword in all_content for keyword in ['script', 'automation', 'tool', 'utility']):
            intent_analysis['project_type'] = 'script_tool'
            intent_analysis['confidence'] += 0.2

        # Complexity level detection
        complexity_indicators = [
            'authentication', 'database', 'user management', 'deployment', 'testing',
            'docker', 'ci/cd', 'production', 'scaling', 'monitoring'
        ]
        complexity_score = sum(1 for indicator in complexity_indicators if indicator in all_content)

        if complexity_score >= 5:
            intent_analysis['complexity_level'] = 'enterprise'
            intent_analysis['confidence'] += 0.2
        elif complexity_score >= 3:
            intent_analysis['complexity_level'] = 'intermediate'
            intent_analysis['confidence'] += 0.1

        # Framework detection from conversation
        framework_keywords = {
            'react': ['react', 'jsx', 'hooks', 'component'],
            'vue': ['vue', 'vuex', 'nuxt'],
            'angular': ['angular', 'typescript'],
            'fastapi': ['fastapi', 'pydantic', 'uvicorn'],
            'flask': ['flask', 'jinja'],
            'express': ['express', 'node.js', 'npm'],
            'django': ['django', 'orm']
        }

        for framework, keywords in framework_keywords.items():
            if any(keyword in all_content for keyword in keywords):
                intent_analysis['primary_frameworks'].append(framework)
                intent_analysis['confidence'] += 0.1

        # Development phase detection
        if any(phrase in all_content for phrase in ['prototype', 'poc', 'proof of concept', 'quick']):
            intent_analysis['development_phase'] = 'prototype'
        elif any(phrase in all_content for phrase in ['production', 'deploy', 'release', 'launch']):
            intent_analysis['development_phase'] = 'production'
        elif any(phrase in all_content for phrase in ['refactor', 'improve', 'optimize', 'enhance']):
            intent_analysis['development_phase'] = 'enhancement'

        # User goals extraction
        goal_patterns = [
            r'(build|create|make|develop)\s+(?:a\s+)?(\w+(?:\s+\w+){0,3})',
            r'(implement|add|setup)\s+(\w+(?:\s+\w+){0,2})',
            r'(need|want|looking for)\s+(?:a\s+)?(\w+(?:\s+\w+){0,3})'
        ]

        import re
        for pattern in goal_patterns:
            matches = re.finditer(pattern, all_content, re.IGNORECASE)
            for match in matches:
                goal = f"{match.group(1)} {match.group(2)}"
                if len(goal.split()) <= 4:  # Keep goals concise
                    intent_analysis['user_goals'].append(goal)

        intent_analysis['confidence'] = min(1.0, intent_analysis['confidence'])
        return intent_analysis

    @staticmethod
    def detect_file_relationships(artifacts: List[tuple]) -> dict:
        """Identify relationships between artifacts for intelligent grouping"""
        relationships = {
            'imports': {},  # File A imports from File B
            'components': {},  # UI components and their relationships
            'configs': [],  # Configuration files
            'tests': {},  # Test files and their targets
            'assets': [],  # Static assets
            'entry_points': [],  # Main entry files
            'related_groups': []  # Files that should be grouped together
        }

        # Analyze each artifact for relationships
        for i, (filename_a, content_a, ext_a) in enumerate(artifacts):

            # Detect entry points
            if any(pattern in content_a.lower() for pattern in [
                'if __name__ == "__main__"', 'app.run()', 'uvicorn.run',
                'createroot', 'reactdom.render', 'new vue'
            ]):
                relationships['entry_points'].append(filename_a)

            # Detect configuration files
            if any(pattern in filename_a.lower() for pattern in [
                'config', 'setting', 'env', 'package.json', 'requirements.txt',
                'dockerfile', 'makefile'
            ]):
                relationships['configs'].append(filename_a)

            # Detect test files
            if 'test' in filename_a.lower() or 'spec' in filename_a.lower():
                # Try to find the target file being tested
                target_name = filename_a.replace('test_', '').replace('_test', '').replace('.test', '').replace('.spec', '')
                for filename_b, _, _ in artifacts:
                    if target_name in filename_b and filename_b != filename_a:
                        relationships['tests'][filename_a] = filename_b
                        break

            # Detect imports and dependencies
            import_patterns = [
                r'import\s+(\w+)',  # Python imports
                r'from\s+["\']([^"\']+)["\']',  # Python from imports
                r'require\(["\']([^"\']+)["\']\)',  # Node.js requires
                r'import\s+.*from\s+["\']([^"\']+)["\']',  # ES6 imports
                r'#include\s*[<"]([^>"]+)[>"]',  # C/C++ includes
                r'use\s+(\w+(?:::\w+)*)',  # Rust use statements
            ]

            imported_files = []
            for pattern in import_patterns:
                import re
                matches = re.finditer(pattern, content_a, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    imported_name = match.group(1)
                    # Look for corresponding files in artifacts
                    for filename_b, _, _ in artifacts:
                        if (imported_name.lower() in filename_b.lower() or
                            filename_b.lower().startswith(imported_name.lower())):
                            imported_files.append(filename_b)

            if imported_files:
                relationships['imports'][filename_a] = imported_files

            # Detect UI components (React, Vue, etc.)
            if any(pattern in content_a.lower() for pattern in [
                'export default', 'component', 'props', 'jsx', 'vue'
            ]):
                component_type = 'unknown'
                if 'export default' in content_a and ('.jsx' in ext_a or '.tsx' in ext_a):
                    component_type = 'react_component'
                elif '<template>' in content_a:
                    component_type = 'vue_component'

                relationships['components'][filename_a] = {
                    'type': component_type,
                    'dependencies': imported_files
                }

        # Group related files
        file_groups = ConversationAnalyzer._generate_file_groups(artifacts, relationships)
        relationships['related_groups'] = file_groups

        return relationships

    @staticmethod
    def _generate_file_groups(artifacts: List[tuple], relationships: dict) -> List[dict]:
        """Generate groups of related files that should be placed together"""
        groups = []

        # Group by feature/module based on naming patterns
        feature_groups = {}
        for filename, content, ext in artifacts:
            # Extract potential feature name from filename
            base_name = filename.lower().replace(ext, '')
            feature_parts = base_name.split('_')

            # Look for common prefixes/patterns
            if len(feature_parts) > 1:
                potential_feature = feature_parts[0]
                if potential_feature not in feature_groups:
                    feature_groups[potential_feature] = []
                feature_groups[potential_feature].append(filename)

        # Convert to group format
        for feature, files in feature_groups.items():
            if len(files) > 1:  # Only group if multiple files
                groups.append({
                    'group_name': feature,
                    'files': files,
                    'suggested_directory': feature
                })

        # Group components with their tests
        for test_file, target_file in relationships.get('tests', {}).items():
            groups.append({
                'group_name': f"{target_file}_with_tests",
                'files': [target_file, test_file],
                'suggested_directory': 'tests' if 'test' in test_file else None
            })

        return groups

    @staticmethod
    def enhance_project_analysis(base_analysis: dict, conversation_data: dict) -> dict:
        """Enhance existing project analysis with conversation context"""
        enhanced_analysis = base_analysis.copy()

        # Analyze conversation intent
        messages = conversation_data.get('messages', [])
        intent = ConversationAnalyzer.analyze_conversation_intent(messages)

        # Analyze file relationships
        artifacts_data = [(a.get('title', ''), a.get('content', ''), a.get('language', ''))
                         for a in conversation_data.get('artifacts', [])]
        relationships = ConversationAnalyzer.detect_file_relationships(artifacts_data)

        # Enhance the analysis
        enhanced_analysis.update({
            'conversation_intent': intent,
            'file_relationships': relationships,
            'enhanced_confidence': min(1.0, base_analysis.get('confidence', 0.0) + intent['confidence'] * 0.3),
            'intelligent_grouping': ConversationAnalyzer._generate_intelligent_structure(
                base_analysis, intent, relationships
            )
        })

        return enhanced_analysis

    @staticmethod
    def _generate_intelligent_structure(base_analysis: dict, intent: dict, relationships: dict) -> dict:
        """Generate intelligent directory structure based on conversation analysis"""
        structure = {}

        project_type = intent.get('project_type', 'unknown')
        complexity = intent.get('complexity_level', 'simple')
        frameworks = intent.get('primary_frameworks', [])

        # Base structure based on project type and complexity
        if project_type == 'web_application':
            if 'react' in frameworks:
                structure = {
                    'src/': 'Source code',
                    'src/components/': 'React components',
                    'src/pages/': 'Page components',
                    'src/hooks/': 'Custom hooks',
                    'src/utils/': 'Utility functions',
                    'src/styles/': 'CSS and styling',
                    'public/': 'Static assets',
                    'tests/': 'Test files'
                }
            elif 'vue' in frameworks:
                structure = {
                    'src/': 'Source code',
                    'src/components/': 'Vue components',
                    'src/views/': 'Page views',
                    'src/router/': 'Routing configuration',
                    'src/store/': 'State management',
                    'src/assets/': 'Static assets',
                    'tests/': 'Test files'
                }
        elif project_type == 'backend_api':
            if 'fastapi' in frameworks:
                structure = {
                    'app/': 'Application code',
                    'app/api/': 'API endpoints',
                    'app/core/': 'Core configuration',
                    'app/models/': 'Data models',
                    'app/services/': 'Business logic',
                    'tests/': 'Test files',
                    'docs/': 'Documentation'
                }

        # Add complexity-based additions
        if complexity == 'enterprise':
            structure.update({
                'deploy/': 'Deployment configurations',
                'scripts/': 'Build and utility scripts',
                'monitoring/': 'Monitoring and logging'
            })

        # Add relationship-based groupings
        for group in relationships.get('related_groups', []):
            if group.get('suggested_directory'):
                structure[f"{group['suggested_directory']}/"] = f"Related files: {', '.join(group['files'])}"

        return structure

class ClaudeArtifactDownloader:
    """Main downloader class with multiple fallback mechanisms"""

    def __init__(self, output_dir: str = "./artifacts", create_structure: bool = True,
                 max_workers: int = 4, rate_limit: float = 1.0, project_structure: bool = False,
                 ml_enhanced: bool = True, conversation_analysis: bool = True):
        self.output_dir = Path(output_dir)
        self.create_structure = create_structure
        self.project_structure = project_structure  # Smart project organization
        self.ml_enhanced = ml_enhanced  # ML-enhanced detection
        self.conversation_analysis = conversation_analysis  # NEW: Conversation-wide analysis
        self.max_workers = max_workers
        self.rate_limit = rate_limit
        self.session = requests.Session()
        self.artifacts: List[Artifact] = []
        self.detected_project_type = ProjectType.UNKNOWN
        self.project_analysis = {}
        self.conversation_data = {}  # Store conversation context

        # Initialize ML detector if enabled
        if self.ml_enhanced:
            self.ml_detector = MLFileTypeDetector()

        # Setup output directory
        self.output_dir.mkdir(exist_ok=True)

        # Configure session with connection pooling and retries
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
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
            # Validate URL format with specific validation
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ConversationParsingError(f"Invalid URL format: {url}", url)

            # Additional Claude.ai URL validation
            if 'claude.ai' not in parsed_url.netloc and 'anthropic.com' not in parsed_url.netloc:
                logger.warning(f"URL doesn't appear to be from Claude.ai: {parsed_url.netloc}")

            logger.info(f"Extracting artifacts from URL: {url}")

            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # Check content size limit to prevent memory issues
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB limit
                raise ConversationParsingError(
                    f"Response too large: {content_length} bytes (max 10MB)", url
                )

            # Check content type for basic validation
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type and 'application/json' not in content_type:
                logger.warning(f"Unexpected content type: {content_type}")

            # Parse conversation data (enhanced with error handling)
            artifacts = self._parse_conversation_page(response.text)

            logger.info(f"Found {len(artifacts)} artifacts via URL extraction")
            return artifacts

        except requests.exceptions.Timeout as e:
            raise ConversationParsingError(f"URL request timed out after 30s: {url}", url) from e
        except requests.exceptions.ConnectionError as e:
            raise ConversationParsingError(f"Connection error for URL {url}: {e}", url) from e
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else "unknown"
            raise ConversationParsingError(
                f"HTTP error {status_code} for URL {url}: {e}", url
            ) from e
        except ConversationParsingError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            # Catch any other unexpected errors
            raise ConversationParsingError(
                f"Unexpected error extracting from URL {url}: {type(e).__name__}: {e}", url
            ) from e

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

        # Method 4: Manual input (with environment check)
        if not self.artifacts and kwargs.get('allow_manual', True):
            # Check if we're in a non-interactive environment
            if not sys.stdin.isatty() or os.getenv('CLAUDE_BATCH_MODE', '').lower() == 'true':
                logger.info("Skipping manual input in non-interactive environment")
            else:
                try:
                    artifacts = self.extract_artifacts_manual_input()
                    self.artifacts.extend(artifacts)
                except (KeyboardInterrupt, EOFError) as e:
                    logger.info(f"Manual input interrupted: {type(e).__name__}")
                except Exception as e:
                    logger.warning(f"Error during manual input: {e}")

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

        # Generate manifest with project analysis
        self._generate_manifest()

        # Generate project summary if ML-enhanced
        if self.ml_enhanced and self.project_structure:
            summary = self.generate_project_summary()
            summary_path = self.output_dir / 'project_analysis.json'
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            logger.info(f"Generated project analysis: {summary_path}")

        return successful, failed

    def _generate_filename(self, artifact: Artifact) -> str:
        """Generate appropriate filename for artifact"""

        # Validate and sanitize title
        if not artifact.title or len(artifact.title.strip()) == 0:
            artifact.title = f"untitled_artifact_{artifact.id}"

        # Security: Prevent path traversal attacks
        title = artifact.title.replace('..', '').replace('/', '').replace('\\', '')

        # Detect proper extension first to enhance title if needed
        if self.ml_enhanced:
            detected_ext, confidence = FileTypeDetector.detect_extension(
                artifact.content,
                artifact.language,
                artifact.filename
            )
            artifact.confidence_score = confidence
        else:
            detected_ext, _ = FileTypeDetector.detect_extension(
                artifact.content,
                artifact.language,
                artifact.filename
            )

        # Get language/type name for title enhancement
        file_type_name = self._get_file_type_name(detected_ext, artifact.language)

        # Enhance title with file type if not already present
        enhanced_title = self._enhance_title_with_type(title, file_type_name, detected_ext)

        # Clean title for filename - more restrictive for security
        # Clean title using cached patterns for filename sanitization
        clean_title = regex_cache.get_pattern(r'[^\w\s.-]').sub('', enhanced_title)
        clean_title = regex_cache.get_pattern(r'[-\s]+').sub('_', clean_title).strip('_')

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

        # Extension was already detected above for title enhancement

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

        # Create advanced project structure if enabled
        if self.project_structure:
            return self._get_project_path_enhanced(artifact, filename)
        # Create simple subdirectory structure if enabled
        elif self.create_structure and artifact.language:
            return f"{artifact.language}/{filename}"

        return filename

    def _get_project_path_enhanced(self, artifact: Artifact, filename: str) -> str:
        """Enhanced project path with conversation-wide analysis and GitHub intelligence"""

        # Use existing logic as fallback
        base_path = self._get_project_path(artifact, filename)

        # Apply conversation analysis if enabled
        if self.conversation_analysis and self.conversation_data:
            # Enhance project analysis with conversation context
            enhanced_analysis = ConversationAnalyzer.enhance_project_analysis(
                self.project_analysis, self.conversation_data
            )

            # Use intelligent grouping if available
            intelligent_structure = enhanced_analysis.get('intelligent_grouping', {})
            if intelligent_structure:
                intelligent_path = self._apply_conversation_intelligence(
                    artifact, filename, enhanced_analysis
                )
                if intelligent_path:
                    return intelligent_path

        return base_path

    def _apply_conversation_intelligence(self, artifact: Artifact, filename: str, analysis: dict) -> Optional[str]:
        """Apply conversation-based intelligence for optimal file placement"""

        relationships = analysis.get('file_relationships', {})
        intent = analysis.get('conversation_intent', {})
        structure = analysis.get('intelligent_grouping', {})

        # Check if file is in a related group
        for group in relationships.get('related_groups', []):
            if filename in group.get('files', []):
                suggested_dir = group.get('suggested_directory')
                if suggested_dir:
                    return f"{suggested_dir}/{filename}"

        # Apply framework-specific intelligent placement
        frameworks = intent.get('primary_frameworks', [])
        project_type = intent.get('project_type', 'unknown')

        # React component placement
        if 'react' in frameworks and filename in relationships.get('components', {}):
            component_info = relationships['components'][filename]
            if component_info.get('type') == 'react_component':
                # Determine if it's a page component or regular component
                if any(keyword in filename.lower() for keyword in ['page', 'view', 'screen']):
                    return f"src/pages/{filename}"
                else:
                    return f"src/components/{filename}"

        # Test file placement
        if filename in relationships.get('tests', {}):
            target_file = relationships['tests'][filename]
            # Place test next to its target file if possible
            if target_file:
                return f"tests/{filename}"

        # Configuration file placement
        if filename in relationships.get('configs', []):
            return f"config/{filename}"

        # Entry point files stay at root level
        if filename in relationships.get('entry_points', []):
            return filename

        # Use structure-based placement if available
        for dir_path, description in structure.items():
            if any(keyword in description.lower() for keyword in [
                artifact.language or '',
                Path(filename).suffix.lstrip('.'),
                filename.lower().split('.')[0]
            ]):
                return f"{dir_path.rstrip('/')}/{filename}"

        return None

    def set_conversation_data(self, conversation_data: dict):
        """Set conversation data for enhanced analysis"""
        self.conversation_data = conversation_data

    def _get_file_type_name(self, extension: str, language: Optional[str] = None) -> str:
        """Get human-readable file type name from extension"""

        # Remove dot from extension for lookup
        ext = extension.lstrip('.')

        # First try language if provided
        if language:
            return language.title()

        # Map common extensions to readable names
        type_names = {
            'py': 'Python',
            'rs': 'Rust',
            'c': 'C',
            'cpp': 'C++',
            'cc': 'C++',
            'cxx': 'C++',
            'h': 'C Header',
            'hpp': 'C++ Header',
            'js': 'JavaScript',
            'ts': 'TypeScript',
            'jsx': 'React',
            'tsx': 'React TypeScript',
            'html': 'HTML',
            'css': 'CSS',
            'scss': 'SCSS',
            'sass': 'Sass',
            'less': 'Less',
            'vue': 'Vue',
            'svelte': 'Svelte',
            'go': 'Go',
            'java': 'Java',
            'kt': 'Kotlin',
            'swift': 'Swift',
            'php': 'PHP',
            'rb': 'Ruby',
            'sh': 'Shell',
            'ps1': 'PowerShell',
            'bat': 'Batch',
            'sql': 'SQL',
            'json': 'JSON',
            'xml': 'XML',
            'yml': 'YAML',
            'yaml': 'YAML',
            'toml': 'TOML',
            'ini': 'INI',
            'conf': 'Config',
            'cfg': 'Config',
            'md': 'Markdown',
            'txt': 'Text',
            'csv': 'CSV',
            'tsv': 'TSV',
            'tex': 'LaTeX',
            'dockerfile': 'Docker',
            'tf': 'Terraform',
            'proto': 'Protocol Buffer',
            'graphql': 'GraphQL',
            'gql': 'GraphQL',
            'sol': 'Solidity',
            'dart': 'Dart',
            'zig': 'Zig',
            'nim': 'Nim',
            'cr': 'Crystal',
            'ex': 'Elixir',
            'hs': 'Haskell',
            'clj': 'Clojure',
            'jl': 'Julia',
            'r': 'R',
            'lua': 'Lua',
            'pl': 'Perl',
            'asm': 'Assembly'
        }

        # Special cases
        if extension == 'Makefile' or extension == 'makefile':
            return 'Makefile'
        elif extension == 'Dockerfile':
            return 'Docker'
        elif extension == 'CMakeLists.txt':
            return 'CMake'

        return type_names.get(ext, ext.upper() if ext else 'Unknown')

    def _enhance_title_with_type(self, title: str, file_type_name: str, extension: str) -> str:
        """Enhance title with file type if not already present"""

        title_lower = title.lower()
        type_lower = file_type_name.lower()

        # Don't add type if already present in title
        if (type_lower in title_lower or
            extension.lstrip('.') in title_lower or
            any(keyword in title_lower for keyword in [
                'script', 'code', 'file', 'program', 'module',
                'function', 'class', 'component', 'config'
            ])):
            return title

        # Add file type to title in a natural way
        if title.strip():
            # Check if title looks like a description
            if len(title.split()) > 2:
                return f"{title} ({file_type_name})"
            else:
                # Short title - add type as suffix
                return f"{title} {file_type_name}"
        else:
            # Empty or minimal title
            return f"{file_type_name} File"

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
        # Pattern explanation: ```(optional_language)\n(content)\n```
        # Groups: 1=language identifier, 2=code content
        code_block_pattern = r'```(\w+)?\n(.*?)\n```'
        matches = regex_cache.get_pattern(code_block_pattern, re.DOTALL).findall(content)

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
        # Pattern explanation: === ARTIFACT: (title) ===\n(content)
        # Groups: 1=artifact title, 2=artifact content
        # Lookahead: stops at next artifact or end of string
        artifact_pattern = r'=== ARTIFACT: (.+?) ===\n(.*?)(?=\n=== ARTIFACT:|$)'
        artifact_matches = regex_cache.get_pattern(artifact_pattern, re.DOTALL).findall(content)

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

    def _get_project_path(self, artifact: Artifact, filename: str) -> str:
        """Generate smart project structure path based on content analysis"""

        # Analyze project type if not already done
        if self.detected_project_type == ProjectType.UNKNOWN:
            self._analyze_project_type()

        # Get file category based on extension and content
        file_category = self._categorize_file(artifact, filename)

        # Build path based on project type and file category
        project_dir = self._get_project_directory_name()
        category_path = self._get_category_path(file_category, filename)

        return f"{project_dir}/{category_path}/{filename}"

    def _analyze_project_type(self) -> ProjectType:
        """Analyze all artifacts to determine overall project type"""
        if not self.ml_enhanced:
            return ProjectType.UNKNOWN

        type_scores = defaultdict(float)

        for artifact in self.artifacts:
            content_lower = artifact.content.lower()

            # Score each project type based on content
            for proj_type, patterns in self.ml_detector.project_patterns.items():
                score = 0.0

                # Check indicators in title/content
                for indicator in patterns['indicators']:
                    if indicator in content_lower or indicator in artifact.title.lower():
                        score += 1.0

                # Check file extension patterns
                _, ext_confidence = FileTypeDetector.detect_extension(
                    artifact.content, artifact.language, artifact.filename
                )
                if any(pattern in artifact.filename or '.' + pattern in artifact.filename
                       for pattern in patterns['file_patterns'] if artifact.filename):
                    score += ext_confidence

                # Check content keywords
                for keyword in patterns['content_keywords']:
                    if keyword in content_lower:
                        score += 0.5

                type_scores[proj_type] += score

        # Determine best project type
        if type_scores:
            self.detected_project_type = max(type_scores.keys(), key=type_scores.get)
            self.project_analysis = dict(type_scores)
        else:
            self.detected_project_type = ProjectType.MIXED

        return self.detected_project_type

    def _categorize_file(self, artifact: Artifact, filename: str) -> str:
        """Categorize file into appropriate directory structure"""

        _, ext = os.path.splitext(filename.lower())
        content_lower = artifact.content.lower()

        # Documentation files
        if ext in ['.md', '.txt', '.rst', '.doc'] or 'readme' in filename.lower():
            return 'docs'

        # Configuration files
        elif ext in ['.json', '.yml', '.yaml', '.toml', '.ini', '.cfg', '.env'] or \
             filename.lower() in ['dockerfile', 'makefile', 'cmake', '.gitignore']:
            return 'config'

        # Test files
        elif 'test' in filename.lower() or 'spec' in filename.lower() or \
             any(test_keyword in content_lower for test_keyword in ['test_', 'it(', 'describe(', 'assert']):
            return 'tests'

        # Script files
        elif ext in ['.sh', '.bat', '.ps1'] or 'script' in filename.lower():
            return 'scripts'

        # Asset files
        elif ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.css', '.scss', '.less']:
            return 'assets'

        # Source code files
        elif ext in ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.rs', '.go', '.rb', '.php']:
            # Further categorize source files
            if any(keyword in content_lower for keyword in ['main(', '__main__', 'if __name__']):
                return 'src/main'
            elif any(keyword in content_lower for keyword in ['class ', 'interface ', 'enum ']):
                return 'src/lib'
            else:
                return 'src'

        # Default to root level
        else:
            return ''

    def _get_project_directory_name(self) -> str:
        """Generate project directory name based on detected type"""

        if self.detected_project_type == ProjectType.WEB_APP:
            return 'web-app'
        elif self.detected_project_type == ProjectType.API_BACKEND:
            return 'api-backend'
        elif self.detected_project_type == ProjectType.DESKTOP_APP:
            return 'desktop-app'
        elif self.detected_project_type == ProjectType.MOBILE_APP:
            return 'mobile-app'
        elif self.detected_project_type == ProjectType.CLI_TOOL:
            return 'cli-tool'
        elif self.detected_project_type == ProjectType.LIBRARY:
            return 'library'
        elif self.detected_project_type == ProjectType.DOCUMENTATION:
            return 'documentation'
        elif self.detected_project_type == ProjectType.CONFIGURATION:
            return 'configuration'
        else:
            return 'project'

    def _get_category_path(self, category: str, filename: str) -> str:
        """Get the appropriate subdirectory path for the file category"""
        if not category:
            return ''

        # Handle nested categories
        if '/' in category:
            return category

        return category

    def _learn_from_user_correction(self, original_detection: str, correct_type: str,
                                   content: str, filename: str):
        """Learn from user corrections to improve future detection"""
        if self.ml_enhanced:
            correction = {
                'original': original_detection,
                'correct': correct_type,
                'content_sample': content[:500],  # Store sample for pattern learning
                'filename': filename,
                'timestamp': time.time()
            }
            self.ml_detector.user_corrections.append(correction)
            self.ml_detector._save_training_data()

    def generate_project_summary(self) -> Dict:
        """Generate a comprehensive project analysis summary"""
        summary = {
            'project_type': self.detected_project_type.value if self.detected_project_type else 'unknown',
            'total_artifacts': len(self.artifacts),
            'file_types': {},
            'confidence_scores': {},
            'project_analysis': self.project_analysis,
            'directory_structure': {},
            'recommendations': []
        }

        # Analyze file types and confidence
        for artifact in self.artifacts:
            ext = Path(artifact.filename or 'unknown').suffix if artifact.filename else 'unknown'
            summary['file_types'][ext] = summary['file_types'].get(ext, 0) + 1

            if hasattr(artifact, 'confidence_score'):
                summary['confidence_scores'][artifact.id] = artifact.confidence_score

        # Generate recommendations based on analysis
        if self.detected_project_type == ProjectType.WEB_APP:
            summary['recommendations'].extend([
                'Consider organizing components into src/components/',
                'Place static assets in assets/ directory',
                'Keep configuration files in config/ directory'
            ])
        elif self.detected_project_type == ProjectType.API_BACKEND:
            summary['recommendations'].extend([
                'Organize routes and controllers in src/api/',
                'Place database models in src/models/',
                'Keep middleware in src/middleware/'
            ])

        return summary

    def generate_github_intelligence(self, content_data: Dict[str, str] = None,
                                   repository_url: str = "") -> Dict[str, Any]:
        """Generate comprehensive GitHub repository intelligence for optimal file placement"""
        intelligence = {
            'project_analysis': {},
            'structure_recommendations': {},
            'file_placement_suggestions': {},
            'framework_detected': 'unknown',
            'confidence_score': 0.0,
            'optimization_suggestions': []
        }

        try:
            # Use existing artifacts if no content_data provided
            if not content_data and self.artifacts:
                content_data = {
                    artifact.filename or f"artifact_{artifact.id}": artifact.content
                    for artifact in self.artifacts
                }

            # Analyze project patterns using existing ML detector
            if self.ml_enhanced and content_data:
                project_analysis = self._analyze_project_with_ml(content_data)
                intelligence['project_analysis'] = project_analysis

                # Extract framework information
                detected_frameworks = project_analysis.get('detected_frameworks', [])
                if detected_frameworks:
                    intelligence['framework_detected'] = detected_frameworks[0]
                    intelligence['confidence_score'] = project_analysis.get('confidence_score', 0.0)

            # Generate structure recommendations based on detected patterns
            structure_recommendations = self._generate_github_structure_recommendations(
                intelligence['framework_detected'],
                self.detected_project_type
            )
            intelligence['structure_recommendations'] = structure_recommendations

            # Generate intelligent file placement suggestions
            if content_data:
                placement_suggestions = self._generate_intelligent_file_placement(
                    content_data, intelligence['framework_detected']
                )
                intelligence['file_placement_suggestions'] = placement_suggestions

            # Generate optimization suggestions
            optimization_suggestions = self._generate_github_optimization_suggestions(
                intelligence['project_analysis'],
                intelligence['framework_detected'],
                self.detected_project_type
            )
            intelligence['optimization_suggestions'] = optimization_suggestions

        except Exception as e:
            logger.error(f"GitHub intelligence generation failed: {e}")
            intelligence['error'] = str(e)

        return intelligence

    def _analyze_project_with_ml(self, content_data: Dict[str, str]) -> Dict[str, Any]:
        """Analyze project using ML-enhanced detection"""
        analysis = {
            'detected_frameworks': [],
            'detected_languages': [],
            'project_patterns': [],
            'confidence_score': 0.0
        }

        # Framework detection patterns
        framework_patterns = {
            'react': ['react', 'jsx', 'usestate', 'useeffect', 'component'],
            'vue': ['vue', 'template', 'script', 'style', 'v-if', 'v-for'],
            'angular': ['angular', 'component', 'service', 'module', '@injectable'],
            'express': ['express', 'app.get', 'app.post', 'router', 'middleware'],
            'flask': ['flask', 'app.route', '@app.route', 'render_template'],
            'django': ['django', 'models.Model', 'views.py', 'urls.py'],
            'fastapi': ['fastapi', 'async def', 'pydantic', '@app.get', '@app.post'],
            'spring': ['@SpringBootApplication', '@RestController', '@Autowired']
        }

        # Language detection patterns
        language_patterns = {
            'javascript': ['.js', 'function', 'const', 'let', 'var', '=>'],
            'typescript': ['.ts', '.tsx', 'interface', 'type', 'implements'],
            'python': ['.py', 'def ', 'import ', 'class ', 'if __name__'],
            'java': ['.java', 'public class', 'public static', 'import java.'],
            'go': ['.go', 'package main', 'func main', 'import ', 'go.mod'],
            'rust': ['.rs', 'fn main', 'use std::', 'pub fn', 'Cargo.toml']
        }

        # Analyze all content
        all_content = ' '.join(content_data.values()).lower()

        # Detect frameworks
        framework_scores = {}
        for framework, patterns in framework_patterns.items():
            score = sum(all_content.count(pattern.lower()) for pattern in patterns)
            if score > 0:
                framework_scores[framework] = score

        # Sort frameworks by score
        sorted_frameworks = sorted(framework_scores.items(), key=lambda x: x[1], reverse=True)
        analysis['detected_frameworks'] = [fw for fw, score in sorted_frameworks[:3]]

        # Detect languages
        language_scores = {}
        for language, patterns in language_patterns.items():
            score = sum(all_content.count(pattern.lower()) for pattern in patterns)
            if score > 0:
                language_scores[language] = score

        sorted_languages = sorted(language_scores.items(), key=lambda x: x[1], reverse=True)
        analysis['detected_languages'] = [lang for lang, score in sorted_languages[:3]]

        # Calculate overall confidence
        total_patterns = sum(framework_scores.values()) + sum(language_scores.values())
        content_length = len(all_content)
        analysis['confidence_score'] = min(total_patterns / max(content_length / 1000, 1), 1.0)

        return analysis

    def _generate_github_structure_recommendations(self, framework: str, project_type: ProjectType) -> Dict[str, Any]:
        """Generate GitHub-style structure recommendations"""
        recommendations = {
            'directory_structure': {},
            'essential_files': [],
            'recommended_files': [],
            'best_practices': []
        }

        # Framework-specific structures
        if framework == 'react':
            recommendations['directory_structure'] = {
                'src/': {
                    'components/': 'React components',
                    'pages/': 'Page components',
                    'hooks/': 'Custom hooks',
                    'utils/': 'Utility functions',
                    'styles/': 'CSS/SCSS files',
                    'assets/': 'Static assets'
                },
                'public/': 'Public static files',
                'tests/': 'Test files'
            }
            recommendations['essential_files'] = ['package.json', 'README.md', '.gitignore']
            recommendations['recommended_files'] = ['tsconfig.json', '.eslintrc', '.prettierrc']

        elif framework in ['flask', 'django', 'fastapi']:
            recommendations['directory_structure'] = {
                'app/': {
                    'models/': 'Data models',
                    'views/': 'View functions',
                    'controllers/': 'Controllers',
                    'services/': 'Business logic',
                    'utils/': 'Utility functions'
                },
                'tests/': 'Test files',
                'docs/': 'Documentation'
            }
            recommendations['essential_files'] = ['requirements.txt', 'README.md', '.gitignore']
            recommendations['recommended_files'] = ['setup.py', '.env.example', 'Dockerfile']

        elif framework == 'express':
            recommendations['directory_structure'] = {
                'src/': {
                    'routes/': 'API routes',
                    'controllers/': 'Request controllers',
                    'middleware/': 'Middleware functions',
                    'models/': 'Data models',
                    'utils/': 'Utility functions'
                },
                'tests/': 'Test files'
            }
            recommendations['essential_files'] = ['package.json', 'README.md', '.gitignore']
            recommendations['recommended_files'] = ['server.js', '.env.example', 'Dockerfile']

        # Add general best practices
        recommendations['best_practices'] = [
            'Keep directory structure shallow (max 4 levels)',
            'Use descriptive directory and file names',
            'Separate concerns (code, tests, docs)',
            'Include comprehensive README.md',
            'Use consistent naming conventions',
            'Add proper .gitignore file',
            'Include LICENSE file for open source'
        ]

        return recommendations

    def _generate_intelligent_file_placement(self, content_data: Dict[str, str], framework: str) -> Dict[str, str]:
        """Generate intelligent file placement suggestions"""
        placement_suggestions = {}

        for filename, content in content_data.items():
            content_lower = content.lower()
            suggested_location = 'src/'  # Default location

            # Framework-specific placement logic
            if framework == 'react':
                if any(pattern in content_lower for pattern in ['component', 'jsx', 'tsx']):
                    if any(pattern in filename.lower() for pattern in ['page', 'view', 'screen']):
                        suggested_location = 'src/pages/'
                    else:
                        suggested_location = 'src/components/'
                elif any(pattern in content_lower for pattern in ['hook', 'usestate', 'useeffect']):
                    suggested_location = 'src/hooks/'
                elif any(pattern in filename.lower() for pattern in ['util', 'helper']):
                    suggested_location = 'src/utils/'
                elif any(pattern in filename.lower() for pattern in ['style', '.css', '.scss']):
                    suggested_location = 'src/styles/'

            elif framework in ['flask', 'django', 'fastapi']:
                if any(pattern in content_lower for pattern in ['class.*model', 'models.model', 'sqlalchemy']):
                    suggested_location = 'app/models/'
                elif any(pattern in content_lower for pattern in ['def.*view', '@app.route', 'request']):
                    suggested_location = 'app/views/'
                elif any(pattern in content_lower for pattern in ['controller', 'business logic']):
                    suggested_location = 'app/controllers/'
                elif 'service' in filename.lower():
                    suggested_location = 'app/services/'

            elif framework == 'express':
                if any(pattern in content_lower for pattern in ['router', 'app.get', 'app.post']):
                    suggested_location = 'src/routes/'
                elif 'controller' in filename.lower():
                    suggested_location = 'src/controllers/'
                elif 'middleware' in filename.lower() or 'middleware' in content_lower:
                    suggested_location = 'src/middleware/'
                elif 'model' in filename.lower():
                    suggested_location = 'src/models/'

            # Common file types
            if any(pattern in filename.lower() for pattern in ['test', 'spec']):
                suggested_location = 'tests/'
            elif any(pattern in filename.lower() for pattern in ['readme', 'doc', 'changelog']):
                suggested_location = './'
            elif any(pattern in filename.lower() for pattern in ['config', 'settings']):
                suggested_location = 'config/'

            placement_suggestions[filename] = suggested_location

        return placement_suggestions

    def _generate_github_optimization_suggestions(self, project_analysis: Dict[str, Any],
                                                framework: str, project_type: ProjectType) -> List[str]:
        """Generate GitHub repository optimization suggestions"""
        suggestions = []

        confidence_score = project_analysis.get('confidence_score', 0.0)

        # Basic suggestions based on analysis quality
        if confidence_score < 0.5:
            suggestions.append("Consider adding more descriptive file names and comments")
            suggestions.append("Include framework-specific configuration files")

        # Framework-specific suggestions
        if framework == 'react':
            suggestions.extend([
                "Add TypeScript support for better type safety",
                "Include ESLint and Prettier configuration",
                "Add React Testing Library for component testing",
                "Consider using Create React App or Vite for project setup"
            ])

        elif framework in ['flask', 'fastapi']:
            suggestions.extend([
                "Add requirements.txt with pinned versions",
                "Include database migration scripts",
                "Add API documentation (Swagger/OpenAPI)",
                "Consider using virtual environments"
            ])

        elif framework == 'express':
            suggestions.extend([
                "Add API documentation with tools like Swagger",
                "Include error handling middleware",
                "Add input validation with libraries like Joi",
                "Consider using TypeScript for better development experience"
            ])

        # General GitHub best practices
        suggestions.extend([
            "Add comprehensive README.md with setup instructions",
            "Include proper .gitignore for your technology stack",
            "Add LICENSE file if open source",
            "Consider adding GitHub Actions for CI/CD",
            "Include issue and pull request templates",
            "Add CONTRIBUTING.md for contributor guidelines"
        ])

        return suggestions

    def apply_intelligent_sorting(self, output_directory: str = None) -> Dict[str, Any]:
        """Apply intelligent sorting to downloaded artifacts"""
        if not output_directory:
            output_directory = str(self.output_dir / "sorted")

        # Generate intelligence
        intelligence = self.generate_github_intelligence()

        # Create sorted directory structure
        sorted_dir = Path(output_directory)
        sorted_dir.mkdir(parents=True, exist_ok=True)

        sorting_results = {
            'total_files': len(self.artifacts),
            'successfully_sorted': 0,
            'failed_sorts': 0,
            'created_directories': set(),
            'placement_decisions': {},
            'intelligence_used': intelligence
        }

        # Apply intelligent placement
        for artifact in self.artifacts:
            try:
                if artifact.filename:
                    suggested_location = intelligence['file_placement_suggestions'].get(
                        artifact.filename, 'src/'
                    )

                    # Create target directory
                    target_dir = sorted_dir / suggested_location
                    target_dir.mkdir(parents=True, exist_ok=True)
                    sorting_results['created_directories'].add(str(target_dir))

                    # Write file to new location
                    target_file = target_dir / artifact.filename
                    with open(target_file, 'w', encoding='utf-8') as f:
                        f.write(artifact.content)

                    sorting_results['successfully_sorted'] += 1
                    sorting_results['placement_decisions'][artifact.filename] = {
                        'original_location': 'artifacts/',
                        'sorted_location': str(target_file),
                        'reason': f"Intelligent placement based on {intelligence['framework_detected']} patterns"
                    }

            except Exception as e:
                logger.error(f"Failed to sort {artifact.filename}: {e}")
                sorting_results['failed_sorts'] += 1

        # Convert set to list for JSON serialization
        sorting_results['created_directories'] = list(sorting_results['created_directories'])

        # Save sorting report
        report_file = sorted_dir / "sorting_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(sorting_results, f, indent=2, default=str)

        logger.info(f"Intelligent sorting completed: {sorting_results['successfully_sorted']}/{sorting_results['total_files']} files sorted")

        return sorting_results

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
    parser.add_argument('--project-structure', action='store_true', help='Enable smart project structure organization')
    parser.add_argument('--no-ml', action='store_true', help='Disable ML-enhanced filetype detection')
    parser.add_argument('--no-clipboard', action='store_true', help='Skip clipboard check')
    parser.add_argument('--no-manual', action='store_true', help='Skip manual input')
    parser.add_argument('--verbose', action='store_true', help='Verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create downloader
    downloader = ClaudeArtifactDownloader(
        output_dir=args.output_dir,
        create_structure=not args.no_structure,
        project_structure=args.project_structure,
        ml_enhanced=not args.no_ml
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

    if args.project_structure and not args.no_ml:
        print(f"Project type detected: {downloader.detected_project_type.value}")
        print(f"Smart project structure: {'enabled' if args.project_structure else 'disabled'}")
        print(f"ML-enhanced detection: {'enabled' if not args.no_ml else 'disabled'}")

    if successful > 0:
        print(f"Check manifest.json for detailed artifact information")
        if args.project_structure and not args.no_ml:
            print(f"Check project_analysis.json for project structure analysis")

if __name__ == '__main__':
    main()