#!/usr/bin/env python3
"""
ARCHITECT Agent v3.0.0 - Repository Structure Design and Validation
Part of ARTIFACTOR enhanced agent coordination system

Capabilities:
- Optimal repository structure design
- Structure coherence validation
- Improvement suggestions
- Best practices enforcement
- Cross-platform compatibility optimization
"""

import os
import sys
import json
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Set
import logging
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import re

@dataclass
class StructureNode:
    """Represents a node in the repository structure"""
    name: str
    type: str  # 'file' or 'directory'
    path: str
    parent: Optional[str] = None
    children: List[str] = None
    metadata: Dict[str, Any] = None
    recommendations: List[str] = None

    def __post_init__(self):
        if self.children is None:
            self.children = []
        if self.metadata is None:
            self.metadata = {}
        if self.recommendations is None:
            self.recommendations = []

@dataclass
class OptimalStructure:
    """Represents an optimal repository structure design"""
    project_type: str
    framework: str
    structure_tree: Dict[str, Any]
    file_placement_rules: Dict[str, str]
    naming_conventions: Dict[str, str]
    best_practices: List[str]
    quality_score: float
    compliance_level: str
    improvement_suggestions: List[str]

@dataclass
class StructureValidation:
    """Results of structure coherence validation"""
    is_coherent: bool
    coherence_score: float
    violations: List[str]
    inconsistencies: List[str]
    optimization_opportunities: List[str]
    structural_depth: int
    organization_quality: float

class ArchitectAgent:
    """ARCHITECT Agent - Handles repository structure design and validation"""

    def __init__(self, coordinator=None):
        self.coordinator = coordinator
        self.agent_name = "ARCHITECT"
        self.version = "3.0.0"

        # Setup logging
        self.logger = self._setup_logging()

        # Architecture patterns database
        self.architecture_patterns = {}
        self.structure_templates = {}
        self.best_practices_db = {}

        # Quality metrics
        self.quality_weights = {
            'depth_penalty': 0.15,
            'naming_consistency': 0.20,
            'logical_grouping': 0.25,
            'convention_adherence': 0.20,
            'maintainability': 0.20
        }

        # Initialize architecture knowledge base
        self._initialize_architecture_patterns()
        self._initialize_structure_templates()
        self._initialize_best_practices()

        self.logger.info(f"ARCHITECT Agent v{self.version} initialized")

    def _setup_logging(self):
        """Setup logging for ARCHITECT agent"""
        logger = logging.getLogger('ARCHITECT_Agent')
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

    def _initialize_architecture_patterns(self):
        """Initialize architecture patterns for different project types"""
        self.architecture_patterns = {
            'react_webapp': {
                'pattern_type': 'component_based',
                'core_principles': ['separation_of_concerns', 'component_isolation', 'state_management'],
                'structure_depth': 3,
                'recommended_modules': ['components', 'pages', 'hooks', 'utils', 'services', 'styles'],
                'anti_patterns': ['deep_nesting', 'mixed_concerns', 'circular_dependencies']
            },
            'vue_webapp': {
                'pattern_type': 'component_based',
                'core_principles': ['single_file_components', 'store_management', 'router_structure'],
                'structure_depth': 3,
                'recommended_modules': ['components', 'views', 'store', 'router', 'assets', 'utils'],
                'anti_patterns': ['god_components', 'prop_drilling', 'mixed_template_logic']
            },
            'angular_webapp': {
                'pattern_type': 'modular_architecture',
                'core_principles': ['feature_modules', 'lazy_loading', 'dependency_injection'],
                'structure_depth': 4,
                'recommended_modules': ['components', 'services', 'guards', 'interceptors', 'models'],
                'anti_patterns': ['monolithic_modules', 'tight_coupling', 'circular_imports']
            },
            'python_api': {
                'pattern_type': 'layered_architecture',
                'core_principles': ['mvc_separation', 'service_layer', 'data_access_layer'],
                'structure_depth': 3,
                'recommended_modules': ['models', 'views', 'controllers', 'services', 'utils', 'config'],
                'anti_patterns': ['fat_controllers', 'database_in_views', 'global_state']
            },
            'nodejs_api': {
                'pattern_type': 'microservice_ready',
                'core_principles': ['route_separation', 'middleware_chain', 'service_isolation'],
                'structure_depth': 3,
                'recommended_modules': ['routes', 'controllers', 'middleware', 'services', 'models', 'utils'],
                'anti_patterns': ['callback_hell', 'monolithic_routes', 'mixed_concerns']
            },
            'mobile_app': {
                'pattern_type': 'screen_based',
                'core_principles': ['screen_navigation', 'state_management', 'platform_separation'],
                'structure_depth': 3,
                'recommended_modules': ['screens', 'components', 'navigation', 'services', 'utils', 'assets'],
                'anti_patterns': ['platform_mixing', 'large_screens', 'navigation_chaos']
            },
            'desktop_app': {
                'pattern_type': 'process_separation',
                'core_principles': ['main_renderer_split', 'ipc_communication', 'window_management'],
                'structure_depth': 3,
                'recommended_modules': ['main', 'renderer', 'shared', 'resources', 'build'],
                'anti_patterns': ['mixed_processes', 'synchronous_ipc', 'resource_leaks']
            },
            'cli_tool': {
                'pattern_type': 'command_based',
                'core_principles': ['command_separation', 'argument_parsing', 'plugin_architecture'],
                'structure_depth': 2,
                'recommended_modules': ['commands', 'utils', 'config', 'plugins'],
                'anti_patterns': ['monolithic_commands', 'global_options', 'hard_dependencies']
            },
            'library_package': {
                'pattern_type': 'api_first',
                'core_principles': ['clean_api', 'minimal_dependencies', 'version_compatibility'],
                'structure_depth': 2,
                'recommended_modules': ['core', 'utils', 'types', 'tests'],
                'anti_patterns': ['api_sprawl', 'heavy_dependencies', 'breaking_changes']
            }
        }

    def _initialize_structure_templates(self):
        """Initialize structure templates for optimal designs"""
        self.structure_templates = {
            'react_webapp': {
                'root': {
                    'public/': {
                        'index.html': {'required': True, 'description': 'Main HTML template'},
                        'favicon.ico': {'required': True, 'description': 'Website favicon'},
                        'manifest.json': {'required': False, 'description': 'PWA manifest'}
                    },
                    'src/': {
                        'components/': {
                            'common/': {'description': 'Reusable components'},
                            'layout/': {'description': 'Layout components'},
                            'ui/': {'description': 'UI-specific components'}
                        },
                        'pages/': {'description': 'Page components'},
                        'hooks/': {'description': 'Custom React hooks'},
                        'services/': {'description': 'API and external services'},
                        'utils/': {'description': 'Utility functions'},
                        'styles/': {'description': 'Global styles and themes'},
                        'assets/': {'description': 'Static assets'},
                        'App.jsx': {'required': True, 'description': 'Main app component'},
                        'index.js': {'required': True, 'description': 'Application entry point'}
                    },
                    'tests/': {
                        'unit/': {'description': 'Unit tests'},
                        'integration/': {'description': 'Integration tests'},
                        'e2e/': {'description': 'End-to-end tests'}
                    },
                    'package.json': {'required': True, 'description': 'Project dependencies'},
                    '.gitignore': {'required': True, 'description': 'Git ignore patterns'},
                    'README.md': {'required': True, 'description': 'Project documentation'}
                }
            },
            'python_api': {
                'root': {
                    'app/': {
                        '__init__.py': {'required': True, 'description': 'Package initialization'},
                        'main.py': {'required': True, 'description': 'Application entry point'},
                        'models/': {
                            '__init__.py': {'required': True},
                            'database.py': {'description': 'Database models'}
                        },
                        'services/': {
                            '__init__.py': {'required': True},
                            'auth.py': {'description': 'Authentication service'}
                        },
                        'api/': {
                            '__init__.py': {'required': True},
                            'routes/': {'description': 'API route definitions'},
                            'middleware/': {'description': 'API middleware'}
                        },
                        'core/': {
                            '__init__.py': {'required': True},
                            'config.py': {'description': 'Configuration management'},
                            'database.py': {'description': 'Database connection'}
                        },
                        'utils/': {
                            '__init__.py': {'required': True}
                        }
                    },
                    'tests/': {
                        '__init__.py': {'required': True},
                        'unit/': {'description': 'Unit tests'},
                        'integration/': {'description': 'Integration tests'},
                        'conftest.py': {'description': 'Pytest configuration'}
                    },
                    'requirements.txt': {'required': True, 'description': 'Python dependencies'},
                    'setup.py': {'required': False, 'description': 'Package setup'},
                    '.env.example': {'required': True, 'description': 'Environment variables template'},
                    'README.md': {'required': True, 'description': 'Project documentation'}
                }
            }
            # Additional templates would be defined here for other project types
        }

    def _initialize_best_practices(self):
        """Initialize best practices database"""
        self.best_practices_db = {
            'general': [
                'Keep directory structure shallow (max 4 levels deep)',
                'Use consistent naming conventions throughout the project',
                'Group related files together logically',
                'Separate concerns (code, tests, documentation, configuration)',
                'Use descriptive directory and file names',
                'Avoid circular dependencies',
                'Include comprehensive documentation',
                'Implement proper error handling',
                'Follow platform-specific conventions'
            ],
            'react_webapp': [
                'Use PascalCase for component names',
                'Keep components small and focused',
                'Separate presentational and container components',
                'Use custom hooks for reusable logic',
                'Implement proper prop validation',
                'Organize by feature, not by file type',
                'Use absolute imports for cleaner code'
            ],
            'python_api': [
                'Follow PEP 8 style guidelines',
                'Use snake_case for functions and variables',
                'Implement proper exception handling',
                'Use type hints for better code clarity',
                'Keep functions small and single-purpose',
                'Use virtual environments',
                'Implement proper logging'
            ],
            'nodejs_api': [
                'Use camelCase for variables and functions',
                'Implement proper error middleware',
                'Use environment variables for configuration',
                'Implement request validation',
                'Use async/await instead of callbacks',
                'Implement proper security measures',
                'Use middleware for cross-cutting concerns'
            ]
        }

    def execute_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute ARCHITECT agent actions"""
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
            self.logger.error(f"ARCHITECT agent action failed: {e}")
            return AgentResponse(
                agent_name=self.agent_name,
                success=False,
                message=f'Action failed: {str(e)}',
                execution_time=time.time() - start_time
            )

    def action_design_optimal_structure(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Design optimal repository structure based on project analysis"""
        self.logger.info("🏗️ Designing optimal repository structure...")

        project_type = params.get('project_type', 'unknown')
        framework = params.get('framework', '')
        existing_files = params.get('existing_files', [])
        content_analysis = params.get('content_analysis', {})
        requirements = params.get('requirements', {})

        try:
            # Get architecture pattern for project type
            if project_type not in self.architecture_patterns:
                # Try to infer from framework or use generic pattern
                project_type = self._infer_project_type_from_framework(framework)

            architecture = self.architecture_patterns.get(project_type, self.architecture_patterns.get('library_package'))

            # Design structure tree
            structure_tree = self._design_structure_tree(project_type, framework, existing_files, requirements)

            # Generate file placement rules
            placement_rules = self._generate_placement_rules(project_type, framework, architecture)

            # Extract naming conventions
            naming_conventions = self._extract_naming_conventions(project_type, framework)

            # Get applicable best practices
            best_practices = self._get_applicable_best_practices(project_type, framework)

            # Calculate quality score
            quality_score = self._calculate_structure_quality(structure_tree, architecture, existing_files)

            # Determine compliance level
            compliance_level = self._determine_structure_compliance_level(quality_score)

            # Generate improvement suggestions
            improvement_suggestions = self._generate_structure_improvements(
                structure_tree, existing_files, architecture, quality_score
            )

            # Create optimal structure object
            optimal_structure = OptimalStructure(
                project_type=project_type,
                framework=framework,
                structure_tree=structure_tree,
                file_placement_rules=placement_rules,
                naming_conventions=naming_conventions,
                best_practices=best_practices,
                quality_score=quality_score,
                compliance_level=compliance_level,
                improvement_suggestions=improvement_suggestions
            )

            return {
                'success': True,
                'message': f'Optimal structure designed for {project_type} project with {compliance_level} compliance',
                'data': {
                    'optimal_structure': asdict(optimal_structure),
                    'design_metadata': {
                        'architecture_pattern': architecture,
                        'template_used': project_type,
                        'files_analyzed': len(existing_files),
                        'design_timestamp': datetime.now().isoformat()
                    }
                }
            }

        except Exception as e:
            self.logger.error(f"Structure design failed: {e}")
            return {
                'success': False,
                'message': f'Structure design failed: {str(e)}'
            }

    def action_validate_structure_coherence(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate structure coherence and consistency"""
        self.logger.info("🔍 Validating structure coherence...")

        current_structure = params.get('current_structure', {})
        project_type = params.get('project_type', '')
        framework = params.get('framework', '')
        file_list = params.get('file_list', [])

        try:
            # Build structure tree from file list
            if not current_structure and file_list:
                current_structure = self._build_structure_from_files(file_list)

            # Analyze structure depth and organization
            depth_analysis = self._analyze_structure_depth(current_structure)

            # Check naming consistency
            naming_analysis = self._analyze_naming_consistency(file_list)

            # Validate logical grouping
            grouping_analysis = self._analyze_logical_grouping(current_structure, project_type)

            # Check convention adherence
            convention_analysis = self._analyze_convention_adherence(current_structure, project_type, framework)

            # Assess maintainability
            maintainability_analysis = self._analyze_maintainability(current_structure, file_list)

            # Calculate coherence score
            coherence_score = self._calculate_coherence_score(
                depth_analysis, naming_analysis, grouping_analysis, convention_analysis, maintainability_analysis
            )

            # Identify violations and inconsistencies
            violations = []
            inconsistencies = []
            optimization_opportunities = []

            # Collect issues from each analysis
            violations.extend(depth_analysis.get('violations', []))
            violations.extend(naming_analysis.get('violations', []))
            inconsistencies.extend(grouping_analysis.get('inconsistencies', []))
            inconsistencies.extend(convention_analysis.get('inconsistencies', []))
            optimization_opportunities.extend(maintainability_analysis.get('opportunities', []))

            # Create validation result
            validation = StructureValidation(
                is_coherent=coherence_score >= 0.7,
                coherence_score=coherence_score,
                violations=violations,
                inconsistencies=inconsistencies,
                optimization_opportunities=optimization_opportunities,
                structural_depth=depth_analysis.get('max_depth', 0),
                organization_quality=grouping_analysis.get('quality_score', 0.0)
            )

            return {
                'success': True,
                'message': f'Structure coherence validation completed. Score: {coherence_score:.2f}',
                'data': {
                    'validation': asdict(validation),
                    'analysis_details': {
                        'depth_analysis': depth_analysis,
                        'naming_analysis': naming_analysis,
                        'grouping_analysis': grouping_analysis,
                        'convention_analysis': convention_analysis,
                        'maintainability_analysis': maintainability_analysis
                    },
                    'validation_timestamp': datetime.now().isoformat()
                }
            }

        except Exception as e:
            self.logger.error(f"Structure coherence validation failed: {e}")
            return {
                'success': False,
                'message': f'Coherence validation failed: {str(e)}'
            }

    def action_suggest_improvements(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest structure improvements based on analysis"""
        self.logger.info("💡 Generating structure improvement suggestions...")

        current_structure = params.get('current_structure', {})
        validation_results = params.get('validation_results', {})
        project_type = params.get('project_type', '')
        framework = params.get('framework', '')
        priority_level = params.get('priority_level', 'medium')  # low, medium, high

        try:
            suggestions = {
                'high_priority': [],
                'medium_priority': [],
                'low_priority': [],
                'quick_wins': [],
                'long_term': []
            }

            # Generate suggestions based on validation results
            if validation_results:
                suggestions.update(self._generate_validation_based_suggestions(validation_results, priority_level))

            # Generate structural improvements
            structural_suggestions = self._generate_structural_suggestions(current_structure, project_type, framework)
            suggestions['medium_priority'].extend(structural_suggestions)

            # Generate naming improvements
            naming_suggestions = self._generate_naming_suggestions(current_structure, framework)
            suggestions['low_priority'].extend(naming_suggestions)

            # Generate organization improvements
            organization_suggestions = self._generate_organization_suggestions(current_structure, project_type)
            suggestions['high_priority'].extend(organization_suggestions)

            # Generate framework-specific suggestions
            if framework:
                framework_suggestions = self._generate_framework_specific_suggestions(current_structure, framework)
                suggestions['medium_priority'].extend(framework_suggestions)

            # Generate modernization suggestions
            modernization_suggestions = self._generate_modernization_suggestions(current_structure, project_type)
            suggestions['long_term'].extend(modernization_suggestions)

            # Generate quick wins
            quick_win_suggestions = self._generate_quick_wins(current_structure)
            suggestions['quick_wins'].extend(quick_win_suggestions)

            # Calculate implementation effort and impact
            implementation_plan = self._create_implementation_plan(suggestions)

            # Priority filtering based on requested level
            filtered_suggestions = self._filter_suggestions_by_priority(suggestions, priority_level)

            return {
                'success': True,
                'message': f'Generated {sum(len(s) for s in suggestions.values())} improvement suggestions',
                'data': {
                    'suggestions': suggestions,
                    'filtered_suggestions': filtered_suggestions,
                    'implementation_plan': implementation_plan,
                    'metadata': {
                        'priority_level': priority_level,
                        'project_type': project_type,
                        'framework': framework,
                        'generation_timestamp': datetime.now().isoformat()
                    }
                }
            }

        except Exception as e:
            self.logger.error(f"Improvement suggestions generation failed: {e}")
            return {
                'success': False,
                'message': f'Suggestions generation failed: {str(e)}'
            }

    # Helper methods for structure design and analysis

    def _infer_project_type_from_framework(self, framework: str) -> str:
        """Infer project type from framework"""
        framework_mapping = {
            'react': 'react_webapp',
            'vue': 'vue_webapp',
            'angular': 'angular_webapp',
            'python': 'python_api',
            'nodejs': 'nodejs_api',
            'express': 'nodejs_api',
            'flask': 'python_api',
            'django': 'python_api'
        }
        return framework_mapping.get(framework.lower(), 'library_package')

    def _design_structure_tree(self, project_type: str, framework: str, existing_files: List[str], requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Design optimal structure tree"""
        if project_type in self.structure_templates:
            base_template = self.structure_templates[project_type]['root'].copy()
        else:
            # Create generic structure
            base_template = {
                'src/': {'description': 'Source code'},
                'tests/': {'description': 'Test files'},
                'docs/': {'description': 'Documentation'},
                'README.md': {'required': True, 'description': 'Project documentation'}
            }

        # Customize based on existing files and requirements
        customized_structure = self._customize_structure_for_files(base_template, existing_files)

        # Add requirement-specific directories
        if requirements:
            customized_structure.update(self._add_requirement_based_structure(requirements))

        return customized_structure

    def _generate_placement_rules(self, project_type: str, framework: str, architecture: Dict[str, Any]) -> Dict[str, str]:
        """Generate file placement rules"""
        rules = {}

        # Base rules for common file types
        base_rules = {
            '*.test.*': 'tests/',
            '*.spec.*': 'tests/',
            'README*': './',
            'LICENSE*': './',
            'CHANGELOG*': './',
            '.gitignore': './',
            'package.json': './',
            'requirements.txt': './',
            'setup.py': './',
            'Dockerfile': './',
            '.env*': './'
        }
        rules.update(base_rules)

        # Project-type specific rules
        if project_type == 'react_webapp':
            react_rules = {
                '*.jsx': 'src/components/',
                '*.tsx': 'src/components/',
                '*Component.*': 'src/components/',
                '*Page.*': 'src/pages/',
                '*Hook.*': 'src/hooks/',
                '*.css': 'src/styles/',
                '*.scss': 'src/styles/',
                '*Service.*': 'src/services/',
                '*Util.*': 'src/utils/'
            }
            rules.update(react_rules)

        elif project_type == 'python_api':
            python_rules = {
                '*model*.py': 'app/models/',
                '*service*.py': 'app/services/',
                '*controller*.py': 'app/controllers/',
                '*route*.py': 'app/api/routes/',
                'config*.py': 'app/core/',
                '*util*.py': 'app/utils/'
            }
            rules.update(python_rules)

        return rules

    def _extract_naming_conventions(self, project_type: str, framework: str) -> Dict[str, str]:
        """Extract naming conventions for project type and framework"""
        conventions = {
            'files': 'lowercase',
            'directories': 'lowercase',
            'classes': 'PascalCase',
            'functions': 'camelCase',
            'variables': 'camelCase'
        }

        # Framework-specific overrides
        if framework == 'python':
            conventions.update({
                'files': 'snake_case',
                'functions': 'snake_case',
                'variables': 'snake_case'
            })
        elif framework in ['react', 'vue', 'angular']:
            conventions.update({
                'components': 'PascalCase',
                'hooks': 'camelCase'
            })

        return conventions

    def _get_applicable_best_practices(self, project_type: str, framework: str) -> List[str]:
        """Get applicable best practices"""
        practices = self.best_practices_db.get('general', []).copy()

        # Add project-type specific practices
        if project_type in self.best_practices_db:
            practices.extend(self.best_practices_db[project_type])

        # Add framework-specific practices
        if framework in self.best_practices_db:
            practices.extend(self.best_practices_db[framework])

        return list(set(practices))  # Remove duplicates

    def _calculate_structure_quality(self, structure_tree: Dict[str, Any], architecture: Dict[str, Any], existing_files: List[str]) -> float:
        """Calculate structure quality score"""
        scores = []

        # Depth score (prefer shallow structures)
        max_depth = self._calculate_max_depth(structure_tree)
        recommended_depth = architecture.get('structure_depth', 3)
        depth_score = max(0, 1.0 - (max_depth - recommended_depth) * 0.2)
        scores.append(depth_score * self.quality_weights['depth_penalty'])

        # Naming consistency score
        naming_score = self._calculate_naming_consistency_score(existing_files)
        scores.append(naming_score * self.quality_weights['naming_consistency'])

        # Logical grouping score
        grouping_score = self._calculate_logical_grouping_score(structure_tree)
        scores.append(grouping_score * self.quality_weights['logical_grouping'])

        # Convention adherence score
        convention_score = self._calculate_convention_adherence_score(structure_tree, architecture)
        scores.append(convention_score * self.quality_weights['convention_adherence'])

        # Maintainability score
        maintainability_score = self._calculate_maintainability_score(structure_tree, existing_files)
        scores.append(maintainability_score * self.quality_weights['maintainability'])

        return sum(scores)

    def _determine_structure_compliance_level(self, quality_score: float) -> str:
        """Determine structure compliance level"""
        if quality_score >= 0.9:
            return "excellent"
        elif quality_score >= 0.75:
            return "good"
        elif quality_score >= 0.5:
            return "fair"
        else:
            return "needs_improvement"

    def _generate_structure_improvements(self, structure_tree: Dict[str, Any], existing_files: List[str], architecture: Dict[str, Any], quality_score: float) -> List[str]:
        """Generate structure improvement suggestions"""
        improvements = []

        if quality_score < 0.5:
            improvements.append("Consider major restructuring to improve organization")

        # Check for missing recommended directories
        recommended_modules = architecture.get('recommended_modules', [])
        existing_dirs = set(path.split('/')[0] for path in existing_files if '/' in path)

        for module in recommended_modules:
            if module not in existing_dirs:
                improvements.append(f"Consider adding '{module}' directory for better organization")

        # Check for anti-patterns
        anti_patterns = architecture.get('anti_patterns', [])
        for pattern in anti_patterns:
            if self._detect_anti_pattern(pattern, structure_tree, existing_files):
                improvements.append(f"Avoid {pattern.replace('_', ' ')} anti-pattern")

        return improvements

    def _build_structure_from_files(self, file_list: List[str]) -> Dict[str, Any]:
        """Build structure tree from file list"""
        structure = {}

        for file_path in file_list:
            parts = Path(file_path).parts
            current = structure

            for part in parts[:-1]:  # All except the last part (filename)
                if part not in current:
                    current[part] = {}
                current = current[part]

            # Add the file
            filename = parts[-1]
            current[filename] = {'type': 'file'}

        return structure

    def _analyze_structure_depth(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze structure depth"""
        max_depth = self._calculate_max_depth(structure)
        violations = []

        if max_depth > 4:
            violations.append(f"Structure too deep ({max_depth} levels). Recommended maximum: 4 levels")

        return {
            'max_depth': max_depth,
            'violations': violations,
            'recommended_max': 4
        }

    def _analyze_naming_consistency(self, file_list: List[str]) -> Dict[str, Any]:
        """Analyze naming consistency"""
        naming_patterns = {
            'camelCase': 0,
            'snake_case': 0,
            'kebab-case': 0,
            'PascalCase': 0
        }

        violations = []

        for file_path in file_list:
            filename = Path(file_path).stem  # filename without extension

            if re.match(r'^[a-z][a-zA-Z0-9]*$', filename):
                naming_patterns['camelCase'] += 1
            elif re.match(r'^[a-z][a-z0-9_]*$', filename):
                naming_patterns['snake_case'] += 1
            elif re.match(r'^[a-z][a-z0-9-]*$', filename):
                naming_patterns['kebab-case'] += 1
            elif re.match(r'^[A-Z][a-zA-Z0-9]*$', filename):
                naming_patterns['PascalCase'] += 1

        # Check for consistency
        dominant_pattern = max(naming_patterns.items(), key=lambda x: x[1])
        consistency_ratio = dominant_pattern[1] / len(file_list) if file_list else 0

        if consistency_ratio < 0.7:
            violations.append("Inconsistent naming patterns across files")

        return {
            'patterns': naming_patterns,
            'dominant_pattern': dominant_pattern[0],
            'consistency_ratio': consistency_ratio,
            'violations': violations
        }

    def _analyze_logical_grouping(self, structure: Dict[str, Any], project_type: str) -> Dict[str, Any]:
        """Analyze logical grouping of files and directories"""
        inconsistencies = []
        quality_score = 1.0

        # Check if files are logically grouped
        # This is a simplified analysis - would be more sophisticated in production

        return {
            'quality_score': quality_score,
            'inconsistencies': inconsistencies
        }

    def _analyze_convention_adherence(self, structure: Dict[str, Any], project_type: str, framework: str) -> Dict[str, Any]:
        """Analyze adherence to conventions with detailed analysis"""
        inconsistencies = []
        adherence_score = 1.0
        conventions_checked = []

        try:
            # Get architecture pattern for the project type
            architecture = self.architecture_patterns.get(project_type, {})
            recommended_modules = architecture.get('recommended_modules', [])

            # Check for recommended modules presence
            structure_str = str(structure).lower()
            missing_modules = []

            for module in recommended_modules:
                if module not in structure_str:
                    missing_modules.append(module)
                    adherence_score -= 0.1
                    inconsistencies.append(f"Missing recommended module: {module}")
                else:
                    conventions_checked.append(f"Found recommended module: {module}")

            # Check for anti-patterns
            anti_patterns = architecture.get('anti_patterns', [])
            detected_anti_patterns = []

            for pattern in anti_patterns:
                if self._detect_anti_pattern(pattern, structure, []):
                    detected_anti_patterns.append(pattern)
                    adherence_score -= 0.15
                    inconsistencies.append(f"Detected anti-pattern: {pattern.replace('_', ' ')}")
                else:
                    conventions_checked.append(f"No {pattern} anti-pattern detected")

            # Framework-specific convention checks
            if framework:
                framework_checks = self._check_framework_conventions(structure, framework)
                adherence_score -= (1 - framework_checks['score'])
                inconsistencies.extend(framework_checks['issues'])
                conventions_checked.extend(framework_checks['passes'])

            # Check core principles adherence
            core_principles = architecture.get('core_principles', [])
            for principle in core_principles:
                principle_check = self._check_principle_adherence(principle, structure, project_type)
                if not principle_check['adhered']:
                    adherence_score -= 0.08
                    inconsistencies.append(f"Principle not followed: {principle.replace('_', ' ')}")
                else:
                    conventions_checked.append(f"Principle followed: {principle.replace('_', ' ')}")

            # Ensure score is between 0 and 1
            adherence_score = max(0.0, min(1.0, adherence_score))

        except Exception as e:
            self.logger.warning(f"Convention adherence analysis error: {e}")
            # Return neutral score on error
            adherence_score = 0.5

        return {
            'adherence_score': adherence_score,
            'inconsistencies': inconsistencies,
            'conventions_checked': conventions_checked,
            'missing_modules': missing_modules if 'missing_modules' in locals() else [],
            'detected_anti_patterns': detected_anti_patterns if 'detected_anti_patterns' in locals() else []
        }

    def _check_framework_conventions(self, structure: Dict[str, Any], framework: str) -> Dict[str, Any]:
        """Check framework-specific conventions"""
        issues = []
        passes = []
        score = 1.0

        if framework == 'react':
            # Check for React-specific conventions
            structure_str = str(structure).lower()

            if 'components' not in structure_str:
                issues.append("React project should have a 'components' directory")
                score -= 0.2
            else:
                passes.append("Has components directory")

            if 'hooks' not in structure_str and 'use' not in structure_str:
                issues.append("Consider adding custom hooks directory")
                score -= 0.1
            else:
                passes.append("Has hooks or custom hooks")

        elif framework == 'python':
            # Check for Python-specific conventions
            if '__init__.py' not in str(structure):
                issues.append("Python packages should have __init__.py files")
                score -= 0.2
            else:
                passes.append("Has __init__.py files")

            structure_lower = str(structure).lower()
            if 'tests' not in structure_lower and 'test_' not in structure_lower:
                issues.append("Python project should have tests directory or test files")
                score -= 0.15
            else:
                passes.append("Has test structure")

        elif framework in ['vue', 'angular', 'nodejs']:
            # Check for Node.js project conventions
            if 'package.json' not in str(structure):
                issues.append("Node.js project should have package.json")
                score -= 0.3
            else:
                passes.append("Has package.json")

        return {
            'score': max(0.0, score),
            'issues': issues,
            'passes': passes
        }

    def _check_principle_adherence(self, principle: str, structure: Dict[str, Any], project_type: str) -> Dict[str, Any]:
        """Check adherence to specific architectural principle"""
        structure_str = str(structure).lower()

        if principle == 'separation_of_concerns':
            # Check if code, tests, and config are separated
            has_separation = ('src' in structure_str or 'app' in structure_str) and \
                           ('test' in structure_str or 'spec' in structure_str)
            return {'adhered': has_separation, 'reason': 'Proper separation of source and tests'}

        elif principle == 'component_isolation':
            # Check if components are properly isolated
            has_isolation = 'components' in structure_str or 'component' in structure_str
            return {'adhered': has_isolation, 'reason': 'Components are isolated'}

        elif principle == 'layered_architecture':
            # Check for proper layering (models, views, controllers)
            has_layers = all(layer in structure_str for layer in ['model', 'view', 'controller']) or \
                        all(layer in structure_str for layer in ['model', 'service', 'route'])
            return {'adhered': has_layers, 'reason': 'Proper layered architecture'}

        elif principle == 'modular_architecture':
            # Check for modular structure
            depth = self._calculate_max_depth(structure)
            has_modules = depth >= 2  # At least some level of organization
            return {'adhered': has_modules, 'reason': 'Modular organization present'}

        # Default: assume adherence if principle not specifically checked
        return {'adhered': True, 'reason': f'Principle {principle} assumed present'}

    def _analyze_maintainability(self, structure: Dict[str, Any], file_list: List[str]) -> Dict[str, Any]:
        """Analyze maintainability aspects"""
        opportunities = []
        maintainability_score = 1.0

        # Check for maintainability issues
        if len(file_list) > 50:  # Large project
            # Look for potential organization issues
            top_level_files = [f for f in file_list if '/' not in f]
            if len(top_level_files) > 10:
                opportunities.append("Consider organizing top-level files into directories")
                maintainability_score -= 0.2

        return {
            'maintainability_score': maintainability_score,
            'opportunities': opportunities
        }

    def _calculate_coherence_score(self, depth_analysis: Dict, naming_analysis: Dict,
                                 grouping_analysis: Dict, convention_analysis: Dict,
                                 maintainability_analysis: Dict) -> float:
        """Calculate overall coherence score"""
        scores = [
            1.0 - len(depth_analysis.get('violations', [])) * 0.2,
            naming_analysis.get('consistency_ratio', 0.0),
            grouping_analysis.get('quality_score', 0.0),
            convention_analysis.get('adherence_score', 0.0),
            maintainability_analysis.get('maintainability_score', 0.0)
        ]

        # Weight the scores
        weights = [0.2, 0.25, 0.25, 0.15, 0.15]
        weighted_score = sum(score * weight for score, weight in zip(scores, weights))

        return max(0.0, min(1.0, weighted_score))

    def _calculate_max_depth(self, structure: Dict[str, Any], current_depth: int = 0) -> int:
        """Calculate maximum depth of structure"""
        if not isinstance(structure, dict):
            return current_depth

        max_depth = current_depth
        for key, value in structure.items():
            if isinstance(value, dict) and key.endswith('/'):  # Directory
                depth = self._calculate_max_depth(value, current_depth + 1)
                max_depth = max(max_depth, depth)

        return max_depth

    def _calculate_naming_consistency_score(self, file_list: List[str]) -> float:
        """Calculate naming consistency score"""
        if not file_list:
            return 1.0

        analysis = self._analyze_naming_consistency(file_list)
        return analysis.get('consistency_ratio', 0.0)

    def _calculate_logical_grouping_score(self, structure_tree: Dict[str, Any]) -> float:
        """Calculate logical grouping score"""
        # Simplified scoring - would be more sophisticated in production
        return 0.8

    def _calculate_convention_adherence_score(self, structure_tree: Dict[str, Any], architecture: Dict[str, Any]) -> float:
        """Calculate convention adherence score"""
        # Simplified scoring - would be more sophisticated in production
        return 0.75

    def _calculate_maintainability_score(self, structure_tree: Dict[str, Any], existing_files: List[str]) -> float:
        """Calculate maintainability score"""
        analysis = self._analyze_maintainability(structure_tree, existing_files)
        return analysis.get('maintainability_score', 0.0)

    def _detect_anti_pattern(self, pattern: str, structure_tree: Dict[str, Any], existing_files: List[str]) -> bool:
        """Detect specific anti-patterns"""
        # Simplified anti-pattern detection
        if pattern == 'deep_nesting':
            return self._calculate_max_depth(structure_tree) > 5
        elif pattern == 'mixed_concerns':
            # Check if files with different purposes are in the same directory
            pass
        elif pattern == 'monolithic_modules':
            # Check for overly large modules
            pass

        return False

    # Additional helper methods for suggestion generation

    def _generate_validation_based_suggestions(self, validation_results: Dict[str, Any], priority_level: str) -> Dict[str, List[str]]:
        """Generate suggestions based on validation results"""
        suggestions = {
            'high_priority': [],
            'medium_priority': [],
            'low_priority': []
        }

        # Extract violations and convert to suggestions
        validation = validation_results.get('validation', {})
        violations = validation.get('violations', [])

        for violation in violations:
            if 'too deep' in violation.lower():
                suggestions['high_priority'].append("Refactor directory structure to reduce nesting depth")
            elif 'naming' in violation.lower():
                suggestions['medium_priority'].append("Standardize file naming conventions")

        return suggestions

    def _generate_structural_suggestions(self, structure: Dict[str, Any], project_type: str, framework: str) -> List[str]:
        """Generate structural improvement suggestions"""
        suggestions = []

        # Add project-type specific suggestions
        if project_type == 'react_webapp':
            if 'components/' not in str(structure):
                suggestions.append("Create a dedicated 'components/' directory for React components")
            if 'hooks/' not in str(structure):
                suggestions.append("Consider adding 'hooks/' directory for custom React hooks")

        return suggestions

    def _generate_naming_suggestions(self, structure: Dict[str, Any], framework: str) -> List[str]:
        """Generate naming improvement suggestions"""
        suggestions = []

        if framework == 'python':
            suggestions.append("Ensure all Python files use snake_case naming convention")
        elif framework in ['react', 'vue']:
            suggestions.append("Use PascalCase for component files and camelCase for utilities")

        return suggestions

    def _generate_organization_suggestions(self, structure: Dict[str, Any], project_type: str) -> List[str]:
        """Generate organization improvement suggestions"""
        return [
            "Group related files together in logical directories",
            "Separate concerns (code, tests, documentation)",
            "Create clear module boundaries"
        ]

    def _generate_framework_specific_suggestions(self, structure: Dict[str, Any], framework: str) -> List[str]:
        """Generate framework-specific suggestions"""
        suggestions = []

        if framework == 'react':
            suggestions.extend([
                "Consider using feature-based directory structure",
                "Separate presentational and container components",
                "Create shared utilities directory"
            ])
        elif framework == 'python':
            suggestions.extend([
                "Follow Python package structure conventions",
                "Include __init__.py files in all packages",
                "Separate models, views, and controllers"
            ])

        return suggestions

    def _generate_modernization_suggestions(self, structure: Dict[str, Any], project_type: str) -> List[str]:
        """Generate modernization suggestions"""
        return [
            "Add comprehensive testing infrastructure",
            "Implement continuous integration workflows",
            "Add code quality and linting configuration",
            "Include security scanning and dependency management"
        ]

    def _generate_quick_wins(self, structure: Dict[str, Any]) -> List[str]:
        """Generate quick win suggestions"""
        return [
            "Add or update README.md with project information",
            "Create .gitignore file if missing",
            "Add basic documentation structure",
            "Standardize file naming conventions"
        ]

    def _create_implementation_plan(self, suggestions: Dict[str, List[str]]) -> Dict[str, Any]:
        """Create implementation plan for suggestions"""
        return {
            'phase_1_immediate': suggestions.get('quick_wins', []),
            'phase_2_short_term': suggestions.get('high_priority', []),
            'phase_3_medium_term': suggestions.get('medium_priority', []),
            'phase_4_long_term': suggestions.get('long_term', []),
            'estimated_effort': {
                'quick_wins': 'Low (1-2 hours)',
                'high_priority': 'Medium (1-2 days)',
                'medium_priority': 'Medium (2-5 days)',
                'long_term': 'High (1-2 weeks)'
            }
        }

    def _filter_suggestions_by_priority(self, suggestions: Dict[str, List[str]], priority_level: str) -> List[str]:
        """Filter suggestions by priority level"""
        if priority_level == 'high':
            return suggestions.get('high_priority', []) + suggestions.get('quick_wins', [])
        elif priority_level == 'medium':
            return suggestions.get('medium_priority', [])
        elif priority_level == 'low':
            return suggestions.get('low_priority', [])
        else:
            # Return all suggestions
            all_suggestions = []
            for category_suggestions in suggestions.values():
                all_suggestions.extend(category_suggestions)
            return all_suggestions

    def _customize_structure_for_files(self, base_template: Dict[str, Any], existing_files: List[str]) -> Dict[str, Any]:
        """Customize structure template based on existing files"""
        # This would analyze existing files and adapt the template
        return base_template

    def _add_requirement_based_structure(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Add structure elements based on requirements"""
        additional_structure = {}

        if requirements.get('testing', False):
            additional_structure['tests/'] = {'description': 'Test files'}

        if requirements.get('documentation', False):
            additional_structure['docs/'] = {'description': 'Documentation'}

        return additional_structure


# Integration example
def integrate_architect_agent_with_coordinator():
    """Example of integrating ARCHITECT agent with coordinator"""
    example_integration = """
    # In claude-artifact-coordinator.py, add to workflows:

    'optimize_repository_structure': [
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
            'agent': 'architect',
            'action': 'validate_structure_coherence',
            'params': params,
            'required': True
        },
        {
            'agent': 'architect',
            'action': 'suggest_improvements',
            'params': params,
            'required': False
        }
    ]
    """
    return example_integration


if __name__ == '__main__':
    # Test the ARCHITECT agent standalone
    print("ARCHITECT Agent v3.0.0 - Testing Repository Structure Design")
    print("=" * 60)

    architect_agent = ArchitectAgent()

    # Test structure design
    test_params = {
        'project_type': 'react_webapp',
        'framework': 'react',
        'existing_files': ['src/App.jsx', 'src/components/Header.jsx', 'public/index.html', 'package.json'],
        'requirements': {'testing': True, 'documentation': True}
    }

    result = architect_agent.action_design_optimal_structure(test_params)
    print("\nStructure Design Result:")
    print(json.dumps(result, indent=2, default=str))

    # Test coherence validation
    validation_params = {
        'file_list': ['src/App.jsx', 'src/components/Header.jsx', 'src/utils/helpers.js'],
        'project_type': 'react_webapp',
        'framework': 'react'
    }

    result2 = architect_agent.action_validate_structure_coherence(validation_params)
    print("\nCoherence Validation Result:")
    print(json.dumps(result2, indent=2, default=str))

    print("\n✅ ARCHITECT Agent testing completed successfully")