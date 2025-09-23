#!/usr/bin/env python3
"""
WEB Agent v3.0.0 - Web Analysis and GitHub Pattern Recognition
Part of ARTIFACTOR enhanced agent coordination system

Capabilities:
- GitHub repository structure analysis
- Framework-specific pattern detection
- Community standard validation
- Web-based artifact intelligence
- Repository sorting optimization
"""

import os
import sys
import json
import time
import requests
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Set
import logging
from dataclasses import dataclass, asdict
from urllib.parse import urlparse, urljoin
import re
from collections import Counter, defaultdict
import asyncio
import aiohttp

@dataclass
class GitHubPattern:
    """Represents a detected GitHub repository pattern"""
    framework: str
    confidence: float
    indicators: List[str]
    file_patterns: List[str]
    directory_structure: Dict[str, List[str]]
    community_score: float = 0.0
    best_practices: List[str] = None

    def __post_init__(self):
        if self.best_practices is None:
            self.best_practices = []

@dataclass
class RepositoryIntelligence:
    """Comprehensive repository intelligence data"""
    project_type: str
    primary_language: str
    framework_detected: str
    structure_quality_score: float
    recommended_structure: Dict[str, Any]
    file_placement_suggestions: Dict[str, str]
    community_alignment: float
    optimization_suggestions: List[str]
    patterns_detected: List[GitHubPattern]

class WebAgent:
    """WEB Agent - Handles web-based analysis and GitHub repository pattern recognition"""

    def __init__(self, coordinator=None):
        self.coordinator = coordinator
        self.agent_name = "WEB"
        self.version = "3.0.0"

        # Setup logging
        self.logger = self._setup_logging()

        # GitHub pattern database
        self.github_patterns_db = {}
        self.framework_conventions = {}
        self.community_standards = {}

        # Performance caching
        self.pattern_cache = {}
        self.cache_ttl = 3600  # 1 hour

        # Initialize patterns
        self._initialize_github_patterns()
        self._initialize_framework_conventions()
        self._initialize_community_standards()

        self.logger.info(f"WEB Agent v{self.version} initialized")

    def _setup_logging(self):
        """Setup logging for WEB agent"""
        logger = logging.getLogger('WEB_Agent')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
            )
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        return logger

    def _initialize_github_patterns(self):
        """Initialize GitHub repository patterns database"""
        self.github_patterns_db = {
            'react_webapp': {
                'indicators': ['react', 'jsx', 'tsx', 'component', 'props', 'state'],
                'file_patterns': ['.jsx', '.tsx', '.js', '.ts'],
                'directory_patterns': ['src/components', 'src/pages', 'src/hooks', 'public'],
                'config_files': ['package.json', 'webpack.config.js', 'tsconfig.json'],
                'structure_score': 0.9
            },
            'vue_webapp': {
                'indicators': ['vue', 'vuex', 'nuxt', 'component', 'template', 'script'],
                'file_patterns': ['.vue', '.js', '.ts'],
                'directory_patterns': ['src/components', 'src/views', 'src/store', 'public'],
                'config_files': ['package.json', 'vue.config.js', 'nuxt.config.js'],
                'structure_score': 0.85
            },
            'angular_webapp': {
                'indicators': ['angular', 'component', 'service', 'module', 'directive'],
                'file_patterns': ['.ts', '.html', '.css', '.scss'],
                'directory_patterns': ['src/app', 'src/assets', 'src/environments'],
                'config_files': ['angular.json', 'package.json', 'tsconfig.json'],
                'structure_score': 0.95
            },
            'python_api': {
                'indicators': ['flask', 'django', 'fastapi', 'api', 'endpoint', 'route'],
                'file_patterns': ['.py'],
                'directory_patterns': ['app', 'models', 'views', 'controllers', 'api'],
                'config_files': ['requirements.txt', 'setup.py', 'pyproject.toml'],
                'structure_score': 0.88
            },
            'nodejs_api': {
                'indicators': ['express', 'koa', 'nest', 'api', 'route', 'controller'],
                'file_patterns': ['.js', '.ts'],
                'directory_patterns': ['src', 'routes', 'controllers', 'middleware', 'models'],
                'config_files': ['package.json', 'server.js', 'app.js'],
                'structure_score': 0.82
            },
            'mobile_app': {
                'indicators': ['react-native', 'flutter', 'ionic', 'mobile', 'native'],
                'file_patterns': ['.dart', '.js', '.tsx', '.swift', '.kotlin'],
                'directory_patterns': ['lib', 'ios', 'android', 'src/screens'],
                'config_files': ['pubspec.yaml', 'package.json', 'android/app/build.gradle'],
                'structure_score': 0.78
            },
            'desktop_app': {
                'indicators': ['electron', 'tauri', 'desktop', 'gui', 'window'],
                'file_patterns': ['.js', '.ts', '.rs', '.py'],
                'directory_patterns': ['src/main', 'src/renderer', 'resources'],
                'config_files': ['package.json', 'Cargo.toml', 'main.js'],
                'structure_score': 0.75
            },
            'cli_tool': {
                'indicators': ['cli', 'command', 'argv', 'argparse', 'commander'],
                'file_patterns': ['.py', '.js', '.go', '.rs'],
                'directory_patterns': ['bin', 'src', 'cmd'],
                'config_files': ['setup.py', 'package.json', 'Cargo.toml'],
                'structure_score': 0.70
            },
            'library_package': {
                'indicators': ['library', 'package', 'module', 'export', 'import'],
                'file_patterns': ['.py', '.js', '.ts', '.rs', '.go'],
                'directory_patterns': ['src', 'lib', 'pkg'],
                'config_files': ['setup.py', 'package.json', 'Cargo.toml', 'go.mod'],
                'structure_score': 0.85
            }
        }

    def _initialize_framework_conventions(self):
        """Initialize framework-specific conventions"""
        self.framework_conventions = {
            'react': {
                'recommended_structure': {
                    'src/': ['components/', 'pages/', 'hooks/', 'utils/', 'services/', 'styles/'],
                    'public/': ['index.html', 'favicon.ico'],
                    'root': ['package.json', 'README.md', '.gitignore']
                },
                'naming_conventions': {
                    'components': 'PascalCase',
                    'files': 'camelCase or kebab-case',
                    'directories': 'camelCase'
                },
                'best_practices': [
                    'Use functional components with hooks',
                    'Implement proper error boundaries',
                    'Follow React folder structure conventions',
                    'Use TypeScript for better type safety'
                ]
            },
            'vue': {
                'recommended_structure': {
                    'src/': ['components/', 'views/', 'store/', 'router/', 'assets/'],
                    'public/': ['index.html'],
                    'root': ['package.json', 'vue.config.js', 'README.md']
                },
                'naming_conventions': {
                    'components': 'PascalCase',
                    'files': 'kebab-case',
                    'directories': 'kebab-case'
                },
                'best_practices': [
                    'Use Composition API for Vue 3+',
                    'Implement proper Vuex/Pinia store structure',
                    'Follow Vue style guide conventions'
                ]
            },
            'angular': {
                'recommended_structure': {
                    'src/app/': ['components/', 'services/', 'models/', 'guards/'],
                    'src/': ['assets/', 'environments/'],
                    'root': ['angular.json', 'package.json', 'tsconfig.json']
                },
                'naming_conventions': {
                    'components': 'kebab-case.component',
                    'services': 'kebab-case.service',
                    'modules': 'kebab-case.module'
                },
                'best_practices': [
                    'Follow Angular style guide',
                    'Use feature modules',
                    'Implement lazy loading',
                    'Use OnPush change detection strategy'
                ]
            },
            'python': {
                'recommended_structure': {
                    'src/': ['main/', 'models/', 'services/', 'utils/'],
                    'tests/': ['unit/', 'integration/'],
                    'root': ['requirements.txt', 'setup.py', 'README.md', '.gitignore']
                },
                'naming_conventions': {
                    'files': 'snake_case',
                    'classes': 'PascalCase',
                    'functions': 'snake_case'
                },
                'best_practices': [
                    'Follow PEP 8 style guide',
                    'Use virtual environments',
                    'Implement proper error handling',
                    'Include comprehensive docstrings'
                ]
            }
        }

    def _initialize_community_standards(self):
        """Initialize community standards for validation"""
        self.community_standards = {
            'documentation': {
                'required_files': ['README.md', 'CHANGELOG.md', 'LICENSE'],
                'recommended_files': ['CONTRIBUTING.md', 'CODE_OF_CONDUCT.md', '.github/ISSUE_TEMPLATE.md'],
                'weight': 0.2
            },
            'configuration': {
                'required_files': ['.gitignore', 'package.json OR requirements.txt OR Cargo.toml'],
                'recommended_files': ['.editorconfig', '.eslintrc', 'prettier.config.js'],
                'weight': 0.15
            },
            'testing': {
                'indicators': ['test', 'spec', '__tests__', 'tests/'],
                'coverage_threshold': 0.8,
                'weight': 0.25
            },
            'ci_cd': {
                'indicators': ['.github/workflows/', '.gitlab-ci.yml', 'Jenkinsfile', '.travis.yml'],
                'weight': 0.15
            },
            'security': {
                'indicators': ['.github/security.md', 'security.txt', 'SECURITY.md'],
                'weight': 0.1
            },
            'structure_organization': {
                'depth_penalty': 0.1,  # Penalty per excessive nesting level
                'max_recommended_depth': 4,
                'weight': 0.15
            }
        }

    def execute_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute WEB agent actions"""
        from dataclasses import dataclass

        @dataclass
        class AgentResponse:
            agent_name: str
            success: bool
            message: str
            data: Optional[Dict[str, Any]] = None
            execution_time: float = 0.0
            timestamp: str = ""

            def __post_init__(self):
                if not self.timestamp:
                    self.timestamp = datetime.now().isoformat()

        start_time = time.time()

        try:
            method_name = f"action_{action}"
            if hasattr(self, method_name):
                method = getattr(self, method_name)
                result = method(params)

                execution_time = time.time() - start_time

                if isinstance(result, dict) and 'success' in result:
                    return AgentResponse(
                        agent_name=self.agent_name,
                        success=result['success'],
                        message=result.get('message', f'Action {action} completed'),
                        data=result.get('data'),
                        execution_time=execution_time
                    )
                else:
                    return AgentResponse(
                        agent_name=self.agent_name,
                        success=True,
                        message=f'Action {action} completed',
                        data=result,
                        execution_time=execution_time
                    )
            else:
                return AgentResponse(
                    agent_name=self.agent_name,
                    success=False,
                    message=f'Unknown action: {action}',
                    execution_time=time.time() - start_time
                )

        except Exception as e:
            self.logger.error(f"WEB agent action failed: {e}")
            return AgentResponse(
                agent_name=self.agent_name,
                success=False,
                message=f'Action failed: {str(e)}',
                execution_time=time.time() - start_time
            )

    def action_analyze_github_patterns(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze GitHub repository patterns from content or URL"""
        self.logger.info("🔍 Analyzing GitHub patterns...")

        content_data = params.get('content_data', {})
        repository_url = params.get('repository_url', '')
        file_list = params.get('file_list', [])

        try:
            detected_patterns = []
            confidence_scores = {}

            # Analyze file patterns
            if file_list:
                file_analysis = self._analyze_file_patterns(file_list)
                detected_patterns.extend(file_analysis['patterns'])
                confidence_scores.update(file_analysis['confidence_scores'])

            # Analyze content patterns
            if content_data:
                content_analysis = self._analyze_content_patterns(content_data)
                detected_patterns.extend(content_analysis['patterns'])
                confidence_scores.update(content_analysis['confidence_scores'])

            # Analyze repository structure if URL provided
            if repository_url:
                try:
                    repo_analysis = self._analyze_repository_url(repository_url)
                    detected_patterns.extend(repo_analysis.get('patterns', []))
                    confidence_scores.update(repo_analysis.get('confidence_scores', {}))
                except Exception as e:
                    self.logger.warning(f"Repository URL analysis failed: {e}")

            # Calculate overall pattern confidence
            overall_confidence = self._calculate_overall_confidence(confidence_scores)

            # Determine primary pattern
            primary_pattern = self._determine_primary_pattern(confidence_scores)

            return {
                'success': True,
                'message': f'GitHub pattern analysis completed. Primary pattern: {primary_pattern}',
                'data': {
                    'detected_patterns': detected_patterns,
                    'confidence_scores': confidence_scores,
                    'primary_pattern': primary_pattern,
                    'overall_confidence': overall_confidence,
                    'analysis_metadata': {
                        'files_analyzed': len(file_list),
                        'content_blocks_analyzed': len(content_data),
                        'repository_analyzed': bool(repository_url)
                    }
                }
            }

        except Exception as e:
            self.logger.error(f"GitHub pattern analysis failed: {e}")
            return {
                'success': False,
                'message': f'Pattern analysis failed: {str(e)}'
            }

    def action_fetch_framework_conventions(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch framework-specific conventions and best practices"""
        self.logger.info("📋 Fetching framework conventions...")

        framework = params.get('framework', '').lower()
        include_community_data = params.get('include_community_data', True)

        try:
            if not framework:
                # Return all available frameworks
                return {
                    'success': True,
                    'message': 'All framework conventions retrieved',
                    'data': {
                        'available_frameworks': list(self.framework_conventions.keys()),
                        'conventions': self.framework_conventions
                    }
                }

            if framework not in self.framework_conventions:
                return {
                    'success': False,
                    'message': f'Framework "{framework}" not found in conventions database'
                }

            conventions = self.framework_conventions[framework].copy()

            # Add community data if requested
            if include_community_data:
                try:
                    community_data = self._fetch_community_standards(framework)
                    conventions['community_standards'] = community_data
                except Exception as e:
                    self.logger.warning(f"Failed to fetch community data for {framework}: {e}")
                    conventions['community_standards'] = {}

            return {
                'success': True,
                'message': f'Framework conventions retrieved for {framework}',
                'data': {
                    'framework': framework,
                    'conventions': conventions,
                    'last_updated': datetime.now().isoformat()
                }
            }

        except Exception as e:
            self.logger.error(f"Framework conventions fetch failed: {e}")
            return {
                'success': False,
                'message': f'Failed to fetch conventions: {str(e)}'
            }

    def action_validate_structure_against_community(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate repository structure against community standards"""
        self.logger.info("✅ Validating structure against community standards...")

        structure_data = params.get('structure_data', {})
        framework = params.get('framework', '')
        strict_mode = params.get('strict_mode', False)

        try:
            validation_results = {
                'overall_score': 0.0,
                'category_scores': {},
                'compliance_issues': [],
                'recommendations': [],
                'best_practice_violations': []
            }

            # Validate against community standards
            for category, standards in self.community_standards.items():
                category_score, issues, recommendations = self._validate_category(
                    structure_data, category, standards, strict_mode
                )

                validation_results['category_scores'][category] = category_score
                validation_results['compliance_issues'].extend(issues)
                validation_results['recommendations'].extend(recommendations)

            # Calculate overall score
            total_weight = sum(std.get('weight', 0) for std in self.community_standards.values())
            weighted_score = sum(
                score * self.community_standards[cat].get('weight', 0)
                for cat, score in validation_results['category_scores'].items()
            )
            validation_results['overall_score'] = weighted_score / total_weight if total_weight > 0 else 0.0

            # Framework-specific validation
            if framework and framework in self.framework_conventions:
                framework_validation = self._validate_framework_specific(structure_data, framework)
                validation_results['framework_specific'] = framework_validation
                validation_results['best_practice_violations'].extend(
                    framework_validation.get('violations', [])
                )

            # Generate compliance level
            compliance_level = self._determine_compliance_level(validation_results['overall_score'])

            return {
                'success': True,
                'message': f'Structure validation completed. Compliance level: {compliance_level}',
                'data': {
                    'validation_results': validation_results,
                    'compliance_level': compliance_level,
                    'framework_analyzed': framework,
                    'strict_mode': strict_mode,
                    'validation_timestamp': datetime.now().isoformat()
                }
            }

        except Exception as e:
            self.logger.error(f"Structure validation failed: {e}")
            return {
                'success': False,
                'message': f'Validation failed: {str(e)}'
            }

    def action_generate_repository_intelligence(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive repository intelligence for optimal file placement"""
        self.logger.info("🧠 Generating repository intelligence...")

        try:
            # Collect all analysis data
            content_data = params.get('content_data', {})
            file_list = params.get('file_list', [])
            repository_url = params.get('repository_url', '')

            # Run comprehensive analysis
            pattern_analysis = self.action_analyze_github_patterns({
                'content_data': content_data,
                'file_list': file_list,
                'repository_url': repository_url
            })

            if not pattern_analysis['success']:
                return pattern_analysis

            primary_pattern = pattern_analysis['data']['primary_pattern']
            detected_framework = self._extract_framework_from_pattern(primary_pattern)

            # Get framework conventions
            conventions_result = self.action_fetch_framework_conventions({
                'framework': detected_framework,
                'include_community_data': True
            })

            # Validate current structure
            structure_validation = self.action_validate_structure_against_community({
                'structure_data': {'files': file_list, 'content': content_data},
                'framework': detected_framework,
                'strict_mode': False
            })

            # Generate file placement suggestions
            placement_suggestions = self._generate_file_placement_suggestions(
                file_list, content_data, detected_framework, primary_pattern
            )

            # Create repository intelligence object
            intelligence = RepositoryIntelligence(
                project_type=primary_pattern,
                primary_language=self._detect_primary_language(file_list, content_data),
                framework_detected=detected_framework,
                structure_quality_score=structure_validation['data']['validation_results']['overall_score'],
                recommended_structure=conventions_result['data']['conventions']['recommended_structure'] if conventions_result['success'] else {},
                file_placement_suggestions=placement_suggestions,
                community_alignment=structure_validation['data']['validation_results']['overall_score'],
                optimization_suggestions=self._generate_optimization_suggestions(pattern_analysis, structure_validation),
                patterns_detected=pattern_analysis['data']['detected_patterns']
            )

            return {
                'success': True,
                'message': f'Repository intelligence generated for {primary_pattern} project',
                'data': {
                    'intelligence': asdict(intelligence),
                    'analysis_components': {
                        'pattern_analysis': pattern_analysis['data'],
                        'structure_validation': structure_validation['data'],
                        'framework_conventions': conventions_result['data'] if conventions_result['success'] else {}
                    },
                    'generation_metadata': {
                        'analysis_timestamp': datetime.now().isoformat(),
                        'confidence_level': pattern_analysis['data']['overall_confidence'],
                        'files_analyzed': len(file_list),
                        'content_blocks_analyzed': len(content_data)
                    }
                }
            }

        except Exception as e:
            self.logger.error(f"Repository intelligence generation failed: {e}")
            return {
                'success': False,
                'message': f'Intelligence generation failed: {str(e)}'
            }

    # Helper methods for analysis

    def _analyze_file_patterns(self, file_list: List[str]) -> Dict[str, Any]:
        """Analyze file patterns to detect project type"""
        pattern_matches = defaultdict(int)
        confidence_scores = {}

        for pattern_name, pattern_data in self.github_patterns_db.items():
            matches = 0
            total_indicators = len(pattern_data['file_patterns'])

            for file_path in file_list:
                file_ext = Path(file_path).suffix.lower()
                if file_ext in pattern_data['file_patterns']:
                    matches += 1

            if total_indicators > 0:
                confidence = (matches / len(file_list)) * pattern_data.get('structure_score', 0.5)
                confidence_scores[pattern_name] = min(confidence, 1.0)
                pattern_matches[pattern_name] = matches

        detected_patterns = [
            GitHubPattern(
                framework=pattern_name,
                confidence=confidence_scores[pattern_name],
                indicators=list(pattern_matches.keys()),
                file_patterns=self.github_patterns_db[pattern_name]['file_patterns'],
                directory_structure={},
                community_score=0.0
            )
            for pattern_name in confidence_scores
            if confidence_scores[pattern_name] > 0.1
        ]

        return {
            'patterns': detected_patterns,
            'confidence_scores': confidence_scores
        }

    def _analyze_content_patterns(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze content patterns to detect technologies and frameworks"""
        pattern_matches = defaultdict(int)
        confidence_scores = {}

        # Combine all content for analysis
        all_content = ""
        for content in content_data.values():
            if isinstance(content, str):
                all_content += content.lower() + " "

        for pattern_name, pattern_data in self.github_patterns_db.items():
            matches = 0
            indicators = pattern_data.get('indicators', [])

            for indicator in indicators:
                matches += all_content.count(indicator.lower())

            if len(indicators) > 0:
                # Normalize by content length and indicator count
                content_length = max(len(all_content), 1)
                confidence = (matches / content_length) * 1000 * pattern_data.get('structure_score', 0.5)
                confidence_scores[pattern_name] = min(confidence, 1.0)
                pattern_matches[pattern_name] = matches

        detected_patterns = [
            GitHubPattern(
                framework=pattern_name,
                confidence=confidence_scores[pattern_name],
                indicators=self.github_patterns_db[pattern_name]['indicators'],
                file_patterns=[],
                directory_structure={},
                community_score=0.0
            )
            for pattern_name in confidence_scores
            if confidence_scores[pattern_name] > 0.05
        ]

        return {
            'patterns': detected_patterns,
            'confidence_scores': confidence_scores
        }

    def _analyze_repository_url(self, repository_url: str) -> Dict[str, Any]:
        """Analyze repository from GitHub URL (if accessible)"""
        # Placeholder for repository URL analysis
        # In a real implementation, this would use GitHub API
        return {
            'patterns': [],
            'confidence_scores': {}
        }

    def _calculate_overall_confidence(self, confidence_scores: Dict[str, float]) -> float:
        """Calculate overall confidence from individual pattern scores"""
        if not confidence_scores:
            return 0.0

        # Use weighted average of top 3 scores
        sorted_scores = sorted(confidence_scores.values(), reverse=True)
        top_scores = sorted_scores[:3]

        if len(top_scores) == 1:
            return top_scores[0]
        elif len(top_scores) == 2:
            return (top_scores[0] * 0.7 + top_scores[1] * 0.3)
        else:
            return (top_scores[0] * 0.5 + top_scores[1] * 0.3 + top_scores[2] * 0.2)

    def _determine_primary_pattern(self, confidence_scores: Dict[str, float]) -> str:
        """Determine the primary project pattern"""
        if not confidence_scores:
            return 'unknown'

        return max(confidence_scores.items(), key=lambda x: x[1])[0]

    def _fetch_community_standards(self, framework: str) -> Dict[str, Any]:
        """Fetch community standards for specific framework"""
        # Placeholder for community standards fetching
        # In a real implementation, this might query APIs or databases
        return {
            'last_updated': datetime.now().isoformat(),
            'source': 'internal_database',
            'standards': self.community_standards
        }

    def _validate_category(self, structure_data: Dict[str, Any], category: str,
                          standards: Dict[str, Any], strict_mode: bool) -> Tuple[float, List[str], List[str]]:
        """Validate structure against specific category standards"""
        score = 1.0
        issues = []
        recommendations = []

        # Basic validation logic - would be more sophisticated in real implementation
        if category == 'documentation':
            required_files = standards.get('required_files', [])
            structure_files = structure_data.get('files', [])

            for req_file in required_files:
                if not any(req_file.lower() in str(f).lower() for f in structure_files):
                    score -= 0.3
                    issues.append(f"Missing required documentation file: {req_file}")
                    recommendations.append(f"Add {req_file} to improve documentation score")

        return max(score, 0.0), issues, recommendations

    def _validate_framework_specific(self, structure_data: Dict[str, Any], framework: str) -> Dict[str, Any]:
        """Validate against framework-specific conventions"""
        violations = []
        recommendations = []
        score = 1.0

        if framework in self.framework_conventions:
            conventions = self.framework_conventions[framework]
            # Add framework-specific validation logic here
            pass

        return {
            'score': score,
            'violations': violations,
            'recommendations': recommendations
        }

    def _determine_compliance_level(self, overall_score: float) -> str:
        """Determine compliance level from overall score"""
        if overall_score >= 0.9:
            return "excellent"
        elif overall_score >= 0.75:
            return "good"
        elif overall_score >= 0.5:
            return "fair"
        else:
            return "needs_improvement"

    def _extract_framework_from_pattern(self, pattern: str) -> str:
        """Extract framework name from pattern"""
        framework_mapping = {
            'react_webapp': 'react',
            'vue_webapp': 'vue',
            'angular_webapp': 'angular',
            'python_api': 'python',
            'nodejs_api': 'nodejs'
        }
        return framework_mapping.get(pattern, pattern.split('_')[0] if '_' in pattern else pattern)

    def _detect_primary_language(self, file_list: List[str], content_data: Dict[str, Any]) -> str:
        """Detect primary programming language"""
        language_extensions = {
            '.js': 'javascript',
            '.ts': 'typescript',
            '.py': 'python',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.vue': 'vue',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php'
        }

        language_counts = Counter()

        for file_path in file_list:
            ext = Path(file_path).suffix.lower()
            if ext in language_extensions:
                language_counts[language_extensions[ext]] += 1

        return language_counts.most_common(1)[0][0] if language_counts else 'unknown'

    def _generate_file_placement_suggestions(self, file_list: List[str], content_data: Dict[str, Any],
                                           framework: str, pattern: str) -> Dict[str, str]:
        """Generate intelligent file placement suggestions"""
        suggestions = {}

        if framework in self.framework_conventions:
            conventions = self.framework_conventions[framework]
            recommended_structure = conventions.get('recommended_structure', {})

            for file_path in file_list:
                file_name = Path(file_path).name.lower()
                file_ext = Path(file_path).suffix.lower()

                # Basic placement logic - would be more sophisticated in real implementation
                if 'component' in file_name or file_ext in ['.jsx', '.tsx', '.vue']:
                    suggestions[file_path] = 'src/components/'
                elif 'test' in file_name or file_name.endswith('.test.js'):
                    suggestions[file_path] = 'tests/'
                elif file_ext == '.py' and 'model' in file_name:
                    suggestions[file_path] = 'src/models/'
                elif file_ext == '.py' and 'service' in file_name:
                    suggestions[file_path] = 'src/services/'
                elif file_name in ['readme.md', 'license', 'changelog.md']:
                    suggestions[file_path] = './'
                else:
                    suggestions[file_path] = 'src/'

        return suggestions

    def _generate_optimization_suggestions(self, pattern_analysis: Dict[str, Any],
                                         structure_validation: Dict[str, Any]) -> List[str]:
        """Generate optimization suggestions based on analysis"""
        suggestions = []

        # Extract confidence and compliance scores
        confidence = pattern_analysis.get('data', {}).get('overall_confidence', 0)
        compliance_score = structure_validation.get('data', {}).get('validation_results', {}).get('overall_score', 0)

        if confidence < 0.7:
            suggestions.append("Consider adding more framework-specific files to improve pattern detection")

        if compliance_score < 0.5:
            suggestions.append("Improve project structure to align with community standards")
            suggestions.append("Add missing documentation files (README.md, LICENSE, etc.)")

        if compliance_score < 0.8:
            suggestions.append("Consider adding automated testing infrastructure")
            suggestions.append("Implement continuous integration workflows")

        return suggestions


# Integration with existing agent system
def integrate_web_agent_with_coordinator():
    """Function to demonstrate how to integrate WEB agent with existing coordinator"""
    example_integration = """
    # In claude-artifact-coordinator.py, add to _initialize_agents method:

    def _initialize_agents(self):
        self.agents = {
            'pygui': PyGUIAgent(self),
            'python_internal': PythonInternalAgent(self),
            'debugger': DebuggerAgent(self),
            'web': WebAgent(self),  # Add WEB agent
            'architect': ArchitectAgent(self)  # Add ARCHITECT agent
        }

    # Add new workflow definitions in _get_tandem_workflow method:

    'analyze_github_structure': [
        {
            'agent': 'web',
            'action': 'analyze_github_patterns',
            'params': params,
            'required': True
        },
        {
            'agent': 'architect',
            'action': 'design_optimal_structure',
            'params': params,
            'required': True
        },
        {
            'agent': 'web',
            'action': 'validate_structure_against_community',
            'params': params,
            'required': True
        }
    ]
    """
    return example_integration


if __name__ == '__main__':
    # Test the WEB agent standalone
    print("WEB Agent v3.0.0 - Testing GitHub Pattern Analysis")
    print("=" * 60)

    web_agent = WebAgent()

    # Test pattern analysis
    test_params = {
        'file_list': ['src/App.jsx', 'src/components/Header.jsx', 'package.json', 'public/index.html'],
        'content_data': {
            'App.jsx': 'import React from "react"; function App() { return <div>Hello</div>; }',
            'package.json': '{"dependencies": {"react": "^18.0.0", "react-dom": "^18.0.0"}}'
        }
    }

    result = web_agent.action_analyze_github_patterns(test_params)
    print("\nPattern Analysis Result:")
    print(json.dumps(result, indent=2, default=str))

    # Test framework conventions
    result2 = web_agent.action_fetch_framework_conventions({'framework': 'react'})
    print("\nFramework Conventions Result:")
    print(json.dumps(result2, indent=2, default=str))

    print("\n✅ WEB Agent testing completed successfully")