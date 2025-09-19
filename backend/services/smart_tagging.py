"""
Smart Tagging Service for ARTIFACTOR v3.0
Automated tag generation and metadata extraction
"""

import asyncio
import logging
import json
from typing import List, Dict, Any, Optional, Set, Tuple
import re
from datetime import datetime
from collections import Counter, defaultdict
import hashlib

# ML and NLP libraries
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans, DBSCAN
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.tag import pos_tag
from nltk.chunk import ne_chunk
from nltk.tree import Tree
import spacy
from textblob import TextBlob

# Database integration
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

# Models
from ..models import Artifact, ArtifactTag, User

# Async processing
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class SmartTaggingService:
    """
    Smart tagging service for automatic tag generation and metadata extraction
    """

    def __init__(self):
        self.nlp_model = None
        self.stop_words = set()
        self.tag_cache = {}
        self.cache_timeout = 3600  # 1 hour
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Tag generation rules and patterns
        self.tech_keywords = self._load_tech_keywords()
        self.framework_patterns = self._load_framework_patterns()
        self.programming_patterns = self._load_programming_patterns()

        # Performance metrics
        self.tagging_metrics = {
            'total_tag_generations': 0,
            'avg_tags_per_artifact': 0,
            'accuracy_feedback': [],
            'processing_times': [],
            'cache_hits': 0
        }

    def _load_tech_keywords(self) -> Dict[str, List[str]]:
        """Load technology-specific keywords for tagging"""
        return {
            'web_development': [
                'html', 'css', 'javascript', 'react', 'vue', 'angular', 'node',
                'express', 'fastify', 'webpack', 'vite', 'babel', 'typescript',
                'sass', 'scss', 'bootstrap', 'tailwind', 'jquery', 'dom',
                'frontend', 'backend', 'fullstack', 'spa', 'pwa', 'ssr'
            ],
            'data_science': [
                'pandas', 'numpy', 'matplotlib', 'seaborn', 'plotly', 'sklearn',
                'tensorflow', 'pytorch', 'keras', 'jupyter', 'notebook',
                'analysis', 'visualization', 'machine learning', 'ml', 'ai',
                'neural network', 'deep learning', 'statistics', 'regression',
                'classification', 'clustering', 'dataset', 'feature'
            ],
            'mobile_development': [
                'android', 'ios', 'react native', 'flutter', 'swift', 'kotlin',
                'java', 'objective-c', 'mobile', 'app', 'smartphone', 'tablet',
                'responsive', 'native', 'hybrid', 'cordova', 'phonegap'
            ],
            'devops': [
                'docker', 'kubernetes', 'ci/cd', 'jenkins', 'gitlab', 'github',
                'deployment', 'container', 'orchestration', 'microservices',
                'aws', 'azure', 'gcp', 'cloud', 'terraform', 'ansible',
                'monitoring', 'logging', 'prometheus', 'grafana'
            ],
            'database': [
                'sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch',
                'database', 'query', 'schema', 'migration', 'orm', 'nosql',
                'relational', 'acid', 'transaction', 'index', 'optimization'
            ],
            'security': [
                'authentication', 'authorization', 'jwt', 'oauth', 'ssl', 'tls',
                'encryption', 'hashing', 'bcrypt', 'security', 'vulnerability',
                'xss', 'csrf', 'sql injection', 'firewall', 'penetration',
                'audit', 'compliance', 'gdpr', 'hipaa'
            ],
            'testing': [
                'test', 'testing', 'unit test', 'integration test', 'e2e',
                'pytest', 'jest', 'mocha', 'chai', 'cypress', 'selenium',
                'mock', 'stub', 'coverage', 'tdd', 'bdd', 'quality assurance'
            ],
            'api_development': [
                'api', 'rest', 'restful', 'graphql', 'endpoint', 'swagger',
                'openapi', 'postman', 'http', 'json', 'xml', 'soap',
                'microservice', 'webhook', 'rate limiting', 'versioning'
            ]
        }

    def _load_framework_patterns(self) -> Dict[str, List[str]]:
        """Load framework-specific patterns"""
        return {
            'react': [
                r'import.*react', r'useState', r'useEffect', r'jsx', r'tsx',
                r'component', r'props', r'state', r'render'
            ],
            'vue': [
                r'<template>', r'<script>', r'<style>', r'vue', r'v-if',
                r'v-for', r'v-model', r'computed', r'methods'
            ],
            'angular': [
                r'@Component', r'@Injectable', r'@NgModule', r'angular',
                r'typescript', r'ng-', r'*ngFor', r'*ngIf'
            ],
            'django': [
                r'from django', r'models\.Model', r'views', r'urls',
                r'settings', r'migrate', r'admin'
            ],
            'flask': [
                r'from flask', r'@app\.route', r'render_template',
                r'request', r'session', r'blueprint'
            ],
            'express': [
                r'express', r'app\.get', r'app\.post', r'middleware',
                r'req', r'res', r'next', r'router'
            ],
            'spring': [
                r'@RestController', r'@Service', r'@Repository',
                r'@Autowired', r'springframework', r'@RequestMapping'
            ]
        }

    def _load_programming_patterns(self) -> Dict[str, List[str]]:
        """Load programming language specific patterns"""
        return {
            'python': [
                r'def\s+\w+', r'class\s+\w+', r'import\s+\w+', r'from\s+\w+',
                r'if\s+__name__\s*==\s*["\']__main__["\']', r'\.py$'
            ],
            'javascript': [
                r'function\s+\w+', r'const\s+\w+', r'let\s+\w+', r'var\s+\w+',
                r'=>', r'console\.log', r'\.js$', r'\.ts$'
            ],
            'java': [
                r'public\s+class', r'public\s+static\s+void\s+main',
                r'import\s+java', r'\.java$', r'@Override', r'@Test'
            ],
            'cpp': [
                r'#include', r'int\s+main', r'std::', r'namespace',
                r'\.cpp$', r'\.hpp$', r'\.h$'
            ],
            'sql': [
                r'SELECT\s+', r'FROM\s+', r'WHERE\s+', r'INSERT\s+INTO',
                r'CREATE\s+TABLE', r'ALTER\s+TABLE', r'\.sql$'
            ]
        }

    async def initialize(self):
        """Initialize smart tagging service"""
        try:
            logger.info("Initializing Smart Tagging Service...")

            # Initialize spaCy model
            await self._initialize_nlp_model()

            # Initialize stop words
            self.stop_words = set(stopwords.words('english'))

            logger.info("Smart Tagging Service initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing smart tagging: {e}")
            raise

    async def _initialize_nlp_model(self):
        """Initialize spaCy NLP model"""
        def load_spacy():
            try:
                return spacy.load("en_core_web_sm")
            except OSError:
                logger.warning("spaCy English model not found")
                return None

        self.nlp_model = await asyncio.get_event_loop().run_in_executor(
            self.executor, load_spacy
        )

    async def generate_tags(
        self,
        content: str,
        title: str = "",
        description: str = "",
        file_type: str = "",
        language: str = "",
        max_tags: int = 10
    ) -> Dict[str, Any]:
        """
        Generate smart tags for artifact content

        Args:
            content: Main content to analyze
            title: Artifact title
            description: Artifact description
            file_type: File type
            language: Programming language
            max_tags: Maximum number of tags to generate

        Returns:
            Dictionary with generated tags and metadata
        """
        start_time = datetime.now()

        try:
            # Create cache key
            cache_key = hashlib.md5(
                f"{content[:500]}{title}{description}{file_type}{language}".encode()
            ).hexdigest()

            # Check cache
            if cache_key in self.tag_cache:
                cache_entry = self.tag_cache[cache_key]
                if datetime.now().timestamp() - cache_entry['timestamp'] < self.cache_timeout:
                    self.tagging_metrics['cache_hits'] += 1
                    return cache_entry['result']

            # Combine all text for analysis
            full_text = f"{title} {description} {content}".strip()

            # Generate tags using multiple strategies
            tag_strategies = [
                self._extract_technology_tags(content, file_type, language),
                self._extract_framework_tags(content),
                self._extract_concept_tags(full_text),
                self._extract_linguistic_tags(full_text),
                self._extract_complexity_tags(content),
                self._extract_domain_tags(full_text)
            ]

            # Execute strategies in parallel
            strategy_results = await asyncio.gather(*tag_strategies)

            # Combine and rank tags
            all_tags = []
            tag_scores = defaultdict(float)

            for strategy_result in strategy_results:
                for tag_info in strategy_result:
                    tag = tag_info['tag']
                    score = tag_info['score']
                    source = tag_info['source']

                    tag_scores[tag] += score
                    all_tags.append({
                        'tag': tag,
                        'score': score,
                        'source': source
                    })

            # Select top tags
            final_tags = self._select_top_tags(tag_scores, max_tags)

            # Generate metadata
            metadata = await self._extract_metadata(content, title, description)

            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            result = {
                'tags': final_tags,
                'metadata': metadata,
                'tag_sources': self._group_tags_by_source(all_tags),
                'processing_time_ms': processing_time,
                'total_candidates': len(tag_scores),
                'timestamp': datetime.now().isoformat()
            }

            # Update metrics
            self.tagging_metrics['total_tag_generations'] += 1
            self.tagging_metrics['avg_tags_per_artifact'] = (
                (self.tagging_metrics['avg_tags_per_artifact'] *
                 (self.tagging_metrics['total_tag_generations'] - 1) + len(final_tags)) /
                self.tagging_metrics['total_tag_generations']
            )
            self.tagging_metrics['processing_times'].append(processing_time)

            # Cache result
            self.tag_cache[cache_key] = {
                'result': result,
                'timestamp': datetime.now().timestamp()
            }

            return result

        except Exception as e:
            logger.error(f"Error generating tags: {e}")
            return {
                'error': str(e),
                'tags': [],
                'timestamp': datetime.now().isoformat()
            }

    async def _extract_technology_tags(
        self, content: str, file_type: str, language: str
    ) -> List[Dict[str, Any]]:
        """Extract technology-specific tags"""
        def extract():
            tags = []
            content_lower = content.lower()

            # Add file type and language as tags
            if file_type:
                tags.append({
                    'tag': file_type.lower(),
                    'score': 1.0,
                    'source': 'file_type'
                })

            if language:
                tags.append({
                    'tag': language.lower(),
                    'score': 1.0,
                    'source': 'language'
                })

            # Check technology keywords
            for category, keywords in self.tech_keywords.items():
                category_score = 0
                matched_keywords = []

                for keyword in keywords:
                    if keyword.lower() in content_lower:
                        category_score += 1
                        matched_keywords.append(keyword)

                # Add category tag if enough keywords match
                if category_score >= 2:
                    tags.append({
                        'tag': category.replace('_', '-'),
                        'score': min(category_score / len(keywords), 1.0),
                        'source': 'technology_analysis'
                    })

                # Add individual technology tags
                for keyword in matched_keywords:
                    tags.append({
                        'tag': keyword.replace(' ', '-').lower(),
                        'score': 0.7,
                        'source': 'technology_keyword'
                    })

            return tags

        return await asyncio.get_event_loop().run_in_executor(self.executor, extract)

    async def _extract_framework_tags(self, content: str) -> List[Dict[str, Any]]:
        """Extract framework-specific tags"""
        def extract():
            tags = []

            for framework, patterns in self.framework_patterns.items():
                matches = 0
                for pattern in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        matches += 1

                if matches > 0:
                    confidence = min(matches / len(patterns), 1.0)
                    tags.append({
                        'tag': framework,
                        'score': confidence,
                        'source': 'framework_analysis'
                    })

            return tags

        return await asyncio.get_event_loop().run_in_executor(self.executor, extract)

    async def _extract_concept_tags(self, text: str) -> List[Dict[str, Any]]:
        """Extract conceptual tags using NLP"""
        def extract():
            tags = []

            try:
                if self.nlp_model:
                    doc = self.nlp_model(text[:10000])  # Limit text length

                    # Extract entities
                    for ent in doc.ents:
                        if ent.label_ in ['ORG', 'PRODUCT', 'EVENT', 'WORK_OF_ART']:
                            tag_name = ent.text.lower().replace(' ', '-')
                            if len(tag_name) > 2 and tag_name not in self.stop_words:
                                tags.append({
                                    'tag': tag_name,
                                    'score': 0.6,
                                    'source': 'named_entity'
                                })

                    # Extract noun phrases
                    for chunk in doc.noun_chunks:
                        if len(chunk.text.split()) <= 3:  # Max 3 words
                            tag_name = chunk.text.lower().replace(' ', '-')
                            if len(tag_name) > 3 and not any(word in self.stop_words for word in chunk.text.split()):
                                tags.append({
                                    'tag': tag_name,
                                    'score': 0.4,
                                    'source': 'noun_phrase'
                                })

            except Exception as e:
                logger.warning(f"Error in concept extraction: {e}")

            return tags

        return await asyncio.get_event_loop().run_in_executor(self.executor, extract)

    async def _extract_linguistic_tags(self, text: str) -> List[Dict[str, Any]]:
        """Extract linguistic features as tags"""
        def extract():
            tags = []

            try:
                # Analyze sentiment
                blob = TextBlob(text)
                polarity = blob.sentiment.polarity

                if polarity > 0.1:
                    tags.append({
                        'tag': 'positive-sentiment',
                        'score': min(polarity, 1.0),
                        'source': 'sentiment_analysis'
                    })
                elif polarity < -0.1:
                    tags.append({
                        'tag': 'negative-sentiment',
                        'score': min(abs(polarity), 1.0),
                        'source': 'sentiment_analysis'
                    })

                # Extract frequent meaningful words
                words = word_tokenize(text.lower())
                words = [word for word in words if word.isalnum() and
                        word not in self.stop_words and len(word) > 3]

                word_freq = Counter(words)
                top_words = word_freq.most_common(5)

                for word, freq in top_words:
                    if freq > 2:  # Word appears multiple times
                        tags.append({
                            'tag': word,
                            'score': min(freq / len(words) * 10, 1.0),
                            'source': 'word_frequency'
                        })

            except Exception as e:
                logger.warning(f"Error in linguistic analysis: {e}")

            return tags

        return await asyncio.get_event_loop().run_in_executor(self.executor, extract)

    async def _extract_complexity_tags(self, content: str) -> List[Dict[str, Any]]:
        """Extract complexity-related tags"""
        def extract():
            tags = []

            try:
                lines = content.split('\n')
                line_count = len(lines)
                char_count = len(content)
                word_count = len(content.split())

                # Code complexity indicators
                function_count = len(re.findall(r'\bdef\b|\bfunction\b|\bclass\b', content, re.IGNORECASE))
                control_structures = len(re.findall(r'\bif\b|\bfor\b|\bwhile\b|\btry\b', content, re.IGNORECASE))
                comment_lines = len([line for line in lines if line.strip().startswith(('#', '//', '/*'))])

                # Determine complexity level
                complexity_score = (function_count * 2 + control_structures + line_count / 50)

                if complexity_score < 5:
                    tags.append({'tag': 'simple', 'score': 0.8, 'source': 'complexity_analysis'})
                elif complexity_score < 15:
                    tags.append({'tag': 'moderate', 'score': 0.7, 'source': 'complexity_analysis'})
                else:
                    tags.append({'tag': 'complex', 'score': 0.9, 'source': 'complexity_analysis'})

                # Size indicators
                if line_count > 100:
                    tags.append({'tag': 'large-file', 'score': 0.6, 'source': 'size_analysis'})
                elif line_count < 20:
                    tags.append({'tag': 'small-file', 'score': 0.5, 'source': 'size_analysis'})

                # Documentation level
                if comment_lines / max(line_count, 1) > 0.2:
                    tags.append({'tag': 'well-documented', 'score': 0.7, 'source': 'documentation_analysis'})

            except Exception as e:
                logger.warning(f"Error in complexity analysis: {e}")

            return tags

        return await asyncio.get_event_loop().run_in_executor(self.executor, extract)

    async def _extract_domain_tags(self, text: str) -> List[Dict[str, Any]]:
        """Extract domain-specific tags"""
        def extract():
            tags = []

            domain_keywords = {
                'machine-learning': ['model', 'training', 'dataset', 'features', 'prediction', 'algorithm'],
                'web-scraping': ['scrape', 'crawl', 'parse', 'extract', 'beautifulsoup', 'requests'],
                'automation': ['script', 'automate', 'schedule', 'batch', 'pipeline', 'workflow'],
                'data-processing': ['process', 'transform', 'clean', 'filter', 'aggregate', 'pipeline'],
                'user-interface': ['ui', 'interface', 'form', 'button', 'input', 'display'],
                'configuration': ['config', 'settings', 'environment', 'parameters', 'options'],
                'documentation': ['readme', 'guide', 'tutorial', 'example', 'documentation', 'help'],
                'testing': ['test', 'unit', 'integration', 'mock', 'assert', 'fixture']
            }

            text_lower = text.lower()

            for domain, keywords in domain_keywords.items():
                matches = sum(1 for keyword in keywords if keyword in text_lower)
                if matches >= 2:
                    score = min(matches / len(keywords) * 2, 1.0)
                    tags.append({
                        'tag': domain,
                        'score': score,
                        'source': 'domain_analysis'
                    })

            return tags

        return await asyncio.get_event_loop().run_in_executor(self.executor, extract)

    def _select_top_tags(self, tag_scores: Dict[str, float], max_tags: int) -> List[Dict[str, Any]]:
        """Select top tags based on scores and diversity"""
        # Sort tags by score
        sorted_tags = sorted(tag_scores.items(), key=lambda x: x[1], reverse=True)

        # Select diverse tags
        selected_tags = []
        selected_words = set()

        for tag, score in sorted_tags:
            if len(selected_tags) >= max_tags:
                break

            # Avoid very similar tags
            tag_words = set(tag.split('-'))
            if not any(word in selected_words for word in tag_words):
                selected_tags.append({
                    'name': tag,
                    'confidence': round(score, 3)
                })
                selected_words.update(tag_words)

        return selected_tags

    def _group_tags_by_source(self, all_tags: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Group tags by their source for analysis"""
        grouped = defaultdict(list)
        for tag_info in all_tags:
            grouped[tag_info['source']].append(tag_info['tag'])
        return dict(grouped)

    async def _extract_metadata(
        self, content: str, title: str, description: str
    ) -> Dict[str, Any]:
        """Extract additional metadata"""
        def extract():
            try:
                metadata = {
                    'estimated_reading_time': max(len(content.split()) / 200, 0.5),  # minutes
                    'content_structure': self._analyze_content_structure(content),
                    'key_topics': self._extract_key_topics(content + " " + title + " " + description),
                    'technical_level': self._estimate_technical_level(content),
                    'content_freshness': self._analyze_content_freshness(content)
                }

                return metadata

            except Exception as e:
                logger.warning(f"Error extracting metadata: {e}")
                return {}

        return await asyncio.get_event_loop().run_in_executor(self.executor, extract)

    def _analyze_content_structure(self, content: str) -> Dict[str, Any]:
        """Analyze the structure of content"""
        lines = content.split('\n')

        return {
            'total_lines': len(lines),
            'empty_lines': len([line for line in lines if not line.strip()]),
            'comment_lines': len([line for line in lines if line.strip().startswith(('#', '//', '/*'))]),
            'has_headers': bool(re.search(r'^#+\s', content, re.MULTILINE)),
            'has_code_blocks': bool(re.search(r'```|~~~', content)),
            'indentation_style': 'tabs' if '\t' in content else 'spaces' if '    ' in content else 'none'
        }

    def _extract_key_topics(self, text: str, max_topics: int = 5) -> List[str]:
        """Extract key topics from text"""
        try:
            # Simple topic extraction using TF-IDF
            vectorizer = TfidfVectorizer(
                max_features=100,
                stop_words='english',
                ngram_range=(1, 2)
            )

            tfidf_matrix = vectorizer.fit_transform([text])
            feature_names = vectorizer.get_feature_names_out()
            tfidf_scores = tfidf_matrix.toarray()[0]

            # Get top terms
            top_indices = np.argsort(tfidf_scores)[::-1][:max_topics]
            topics = [feature_names[i] for i in top_indices if tfidf_scores[i] > 0]

            return topics

        except Exception:
            return []

    def _estimate_technical_level(self, content: str) -> str:
        """Estimate technical complexity level"""
        technical_indicators = [
            len(re.findall(r'\bclass\b|\bdef\b|\bfunction\b', content, re.IGNORECASE)),
            len(re.findall(r'\bimport\b|\brequire\b|\binclude\b', content, re.IGNORECASE)),
            len(re.findall(r'\btry\b|\bcatch\b|\bexcept\b', content, re.IGNORECASE)),
            len(re.findall(r'\basync\b|\bawait\b|\bpromise\b', content, re.IGNORECASE))
        ]

        total_indicators = sum(technical_indicators)

        if total_indicators < 3:
            return 'beginner'
        elif total_indicators < 10:
            return 'intermediate'
        else:
            return 'advanced'

    def _analyze_content_freshness(self, content: str) -> str:
        """Analyze if content uses modern practices"""
        modern_patterns = [
            r'\basync\b|\bawait\b',
            r'\bconst\b|\blet\b',
            r'\bimport\s+.*\s+from\b',
            r'=>',
            r'\bTypescript\b|\bTS\b',
            r'\bES6\b|\bES2015\b'
        ]

        modern_count = sum(1 for pattern in modern_patterns if re.search(pattern, content, re.IGNORECASE))

        if modern_count >= 3:
            return 'modern'
        elif modern_count >= 1:
            return 'mixed'
        else:
            return 'traditional'

    async def suggest_tags_for_project(
        self, artifacts: List[Dict[str, Any]], max_suggestions: int = 15
    ) -> List[Dict[str, Any]]:
        """Suggest tags for a collection of artifacts (project-level tagging)"""
        try:
            all_content = []
            for artifact in artifacts:
                content = f"{artifact.get('title', '')} {artifact.get('description', '')} {artifact.get('content', '')}"
                all_content.append(content)

            # Combine all content
            combined_content = " ".join(all_content)

            # Generate project-level tags
            result = await self.generate_tags(
                content=combined_content,
                max_tags=max_suggestions
            )

            # Add project-specific analysis
            project_analysis = {
                'total_artifacts': len(artifacts),
                'dominant_languages': self._analyze_project_languages(artifacts),
                'project_size': self._classify_project_size(artifacts),
                'suggested_tags': result['tags']
            }

            return project_analysis

        except Exception as e:
            logger.error(f"Error suggesting project tags: {e}")
            return {'error': str(e)}

    def _analyze_project_languages(self, artifacts: List[Dict[str, Any]]) -> List[str]:
        """Analyze dominant programming languages in project"""
        language_count = Counter()

        for artifact in artifacts:
            language = artifact.get('language', '').lower()
            if language:
                language_count[language] += 1

        return [lang for lang, count in language_count.most_common(3)]

    def _classify_project_size(self, artifacts: List[Dict[str, Any]]) -> str:
        """Classify project size based on artifact count and complexity"""
        total_artifacts = len(artifacts)
        total_lines = sum(
            len(artifact.get('content', '').split('\n'))
            for artifact in artifacts
        )

        if total_artifacts <= 5 or total_lines <= 500:
            return 'small'
        elif total_artifacts <= 20 or total_lines <= 2000:
            return 'medium'
        else:
            return 'large'

    async def get_tagging_analytics(self) -> Dict[str, Any]:
        """Get tagging performance analytics"""
        return {
            'metrics': self.tagging_metrics.copy(),
            'cache_stats': {
                'cache_size': len(self.tag_cache),
                'cache_timeout_seconds': self.cache_timeout
            },
            'available_categories': list(self.tech_keywords.keys()),
            'supported_frameworks': list(self.framework_patterns.keys())
        }

    async def cleanup(self):
        """Cleanup resources"""
        self.executor.shutdown(wait=True)

# Global instance
smart_tagging_service = SmartTaggingService()