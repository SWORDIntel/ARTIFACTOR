"""
ML Classification Service for ARTIFACTOR v3.0
Advanced content classification with >85% accuracy target
"""

import asyncio
import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import pickle
import hashlib
from datetime import datetime, timedelta
import re

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import joblib

# NLP libraries
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import PorterStemmer, WordNetLemmatizer
import spacy
from textblob import TextBlob
from langdetect import detect, LangDetectError

# Transformers for advanced embeddings
from sentence_transformers import SentenceTransformer
from transformers import pipeline

# Async processing
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Configuration
from ..config import settings

logger = logging.getLogger(__name__)

class MLContentClassifier:
    """
    Advanced ML content classifier for artifacts
    Provides content analysis, language detection, and smart categorization
    """

    def __init__(self):
        self.models = {}
        self.vectorizers = {}
        self.embeddings_model = None
        self.nlp_models = {}
        self.stemmer = PorterStemmer()
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set()
        self.model_cache = {}
        self.cache_timeout = timedelta(hours=1)
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Model performance tracking
        self.performance_metrics = {
            'total_classifications': 0,
            'accuracy_scores': [],
            'processing_times': [],
            'cache_hits': 0
        }

    async def initialize(self):
        """Initialize ML models and download required resources"""
        try:
            logger.info("Initializing ML Content Classifier...")

            # Download NLTK resources
            await self._download_nltk_resources()

            # Initialize spaCy model
            await self._initialize_spacy()

            # Initialize sentence transformer for embeddings
            await self._initialize_embeddings()

            # Load or train classification models
            await self._load_classification_models()

            # Initialize stop words
            self.stop_words = set(stopwords.words('english'))

            logger.info("ML Content Classifier initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing ML classifier: {e}")
            raise

    async def _download_nltk_resources(self):
        """Download required NLTK resources"""
        resources = ['punkt', 'stopwords', 'wordnet', 'omw-1.4', 'vader_lexicon']

        def download_resources():
            for resource in resources:
                try:
                    nltk.download(resource, quiet=True)
                except Exception as e:
                    logger.warning(f"Failed to download NLTK resource {resource}: {e}")

        await asyncio.get_event_loop().run_in_executor(self.executor, download_resources)

    async def _initialize_spacy(self):
        """Initialize spaCy NLP model"""
        def load_spacy():
            try:
                # Try to load English model
                return spacy.load("en_core_web_sm")
            except OSError:
                logger.warning("spaCy English model not found. Please install: python -m spacy download en_core_web_sm")
                return None

        self.nlp_models['spacy'] = await asyncio.get_event_loop().run_in_executor(
            self.executor, load_spacy
        )

    async def _initialize_embeddings(self):
        """Initialize sentence transformer model for embeddings"""
        def load_embeddings():
            try:
                # Use a lightweight model for production
                return SentenceTransformer('all-MiniLM-L6-v2')
            except Exception as e:
                logger.warning(f"Failed to load sentence transformer: {e}")
                return None

        self.embeddings_model = await asyncio.get_event_loop().run_in_executor(
            self.executor, load_embeddings
        )

    async def _load_classification_models(self):
        """Load or train classification models"""
        # For now, we'll create basic models. In production, these would be
        # trained on actual artifact data

        # Programming language classifier
        self.models['language'] = await self._create_language_classifier()

        # Content type classifier
        self.models['content_type'] = await self._create_content_type_classifier()

        # Project category classifier
        self.models['project_category'] = await self._create_project_category_classifier()

        # Quality/complexity classifier
        self.models['quality'] = await self._create_quality_classifier()

    async def _create_language_classifier(self) -> Pipeline:
        """Create programming language classification model"""
        # Training data for programming languages
        training_data = [
            # Python samples
            ("import numpy as np\nfrom sklearn import", "python"),
            ("def function_name(param):\n    return param", "python"),
            ("class MyClass:\n    def __init__(self):", "python"),
            ("for i in range(10):\n    print(i)", "python"),

            # JavaScript samples
            ("function myFunction() {\n    return true;\n}", "javascript"),
            ("const myVar = () => {\n    console.log('hello');\n}", "javascript"),
            ("import React from 'react';\nexport default", "javascript"),
            ("document.getElementById('myId').innerHTML", "javascript"),

            # HTML samples
            ("<!DOCTYPE html>\n<html>\n<head>", "html"),
            ("<div class='container'>\n    <p>Hello", "html"),
            ("<script src='app.js'></script>", "html"),

            # CSS samples
            (".container {\n    display: flex;\n    justify-content: center;", "css"),
            ("@media screen and (max-width: 768px)", "css"),
            ("body {\n    margin: 0;\n    padding: 0;", "css"),

            # SQL samples
            ("SELECT * FROM users WHERE id =", "sql"),
            ("CREATE TABLE artifacts (\n    id UUID PRIMARY KEY", "sql"),
            ("INSERT INTO table_name (column1, column2)", "sql"),

            # Markdown samples
            ("# Heading 1\n## Heading 2\n### Heading 3", "markdown"),
            ("**bold text** and *italic text*", "markdown"),
            ("```python\nprint('hello')\n```", "markdown"),

            # JSON samples
            ('{\n    "name": "value",\n    "array": [1, 2, 3]', "json"),
            ('{"api": {"version": "1.0"}}', "json"),

            # YAML samples
            ("name: my-app\nversion: 1.0.0\ndependencies:", "yaml"),
            ("services:\n  web:\n    image: nginx", "yaml"),

            # Shell/Bash samples
            ("#!/bin/bash\necho 'Hello World'\nif [ $? -eq 0 ]", "shell"),
            ("export PATH=$PATH:/usr/local/bin", "shell"),
        ]

        # Extract features and labels
        texts, labels = zip(*training_data)

        # Create pipeline with TF-IDF and ensemble classifier
        pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(
                max_features=1000,
                ngram_range=(1, 3),
                token_pattern=r'\b\w+\b|[{}()\[\]<>/=+\-*&|!@#$%^]'
            )),
            ('classifier', VotingClassifier([
                ('nb', MultinomialNB()),
                ('svm', SVC(kernel='linear', probability=True)),
                ('rf', RandomForestClassifier(n_estimators=100))
            ]))
        ])

        # Train the model
        def train_model():
            pipeline.fit(texts, labels)
            return pipeline

        return await asyncio.get_event_loop().run_in_executor(self.executor, train_model)

    async def _create_content_type_classifier(self) -> Pipeline:
        """Create content type classification model"""
        training_data = [
            # Documentation
            ("# API Documentation\nThis document describes", "documentation"),
            ("## Installation\nTo install this package", "documentation"),
            ("### Usage Examples\nHere are some examples", "documentation"),

            # Configuration
            ("server:\n  host: localhost\n  port: 8000", "configuration"),
            ("{\n    \"database\": {\n        \"host\":", "configuration"),
            ("export const config = {\n    apiUrl:", "configuration"),

            # Source Code
            ("class DataProcessor {\n    constructor(", "source_code"),
            ("def process_data(input_data):\n    result =", "source_code"),
            ("function calculateTotal(items) {\n    return", "source_code"),

            # Test Code
            ("describe('User authentication', () => {\n    it('should", "test_code"),
            ("def test_user_creation():\n    user = create_user(", "test_code"),
            ("@pytest.fixture\ndef mock_database():", "test_code"),

            # Data/Schema
            ("CREATE TABLE users (\n    id SERIAL PRIMARY KEY", "data_schema"),
            ("{\n    \"$schema\": \"http://json-schema.org", "data_schema"),
            ("type User = {\n    id: number;\n    name: string;", "data_schema"),

            # Scripts/Automation
            ("#!/bin/bash\nset -e\necho 'Building project'", "script"),
            ("name: CI/CD Pipeline\non:\n  push:", "script"),
            ("version: '3.8'\nservices:\n  web:", "script"),
        ]

        texts, labels = zip(*training_data)

        pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(
                max_features=800,
                ngram_range=(1, 2),
                stop_words='english'
            )),
            ('classifier', VotingClassifier([
                ('nb', MultinomialNB()),
                ('rf', RandomForestClassifier(n_estimators=50))
            ]))
        ])

        def train_model():
            pipeline.fit(texts, labels)
            return pipeline

        return await asyncio.get_event_loop().run_in_executor(self.executor, train_model)

    async def _create_project_category_classifier(self) -> Pipeline:
        """Create project category classification model"""
        training_data = [
            # Web Development
            ("React component with hooks useState useEffect", "web_development"),
            ("Express.js server with MongoDB database", "web_development"),
            ("HTML form with CSS styling and JavaScript", "web_development"),

            # Data Science
            ("pandas DataFrame analysis with matplotlib visualization", "data_science"),
            ("machine learning model using scikit-learn", "data_science"),
            ("data preprocessing and feature engineering", "data_science"),

            # DevOps/Infrastructure
            ("Docker container with nginx configuration", "devops"),
            ("Kubernetes deployment with service mesh", "devops"),
            ("CI/CD pipeline with automated testing", "devops"),

            # Mobile Development
            ("React Native component with navigation", "mobile_development"),
            ("Android activity with fragment lifecycle", "mobile_development"),
            ("iOS Swift view controller with constraints", "mobile_development"),

            # API Development
            ("REST API endpoints with authentication", "api_development"),
            ("GraphQL schema with resolvers", "api_development"),
            ("OpenAPI specification with validation", "api_development"),

            # Database
            ("PostgreSQL schema with indexes and constraints", "database"),
            ("MongoDB aggregation pipeline with lookup", "database"),
            ("SQL queries with joins and subqueries", "database"),

            # Security
            ("JWT authentication with bcrypt password hashing", "security"),
            ("OAuth2 implementation with PKCE flow", "security"),
            ("encryption and decryption with AES", "security"),

            # Testing
            ("unit tests with pytest fixtures and mocks", "testing"),
            ("integration tests with database transactions", "testing"),
            ("end-to-end tests with selenium automation", "testing"),
        ]

        texts, labels = zip(*training_data)

        pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(
                max_features=600,
                ngram_range=(1, 2),
                stop_words='english'
            )),
            ('classifier', RandomForestClassifier(n_estimators=100))
        ])

        def train_model():
            pipeline.fit(texts, labels)
            return pipeline

        return await asyncio.get_event_loop().run_in_executor(self.executor, train_model)

    async def _create_quality_classifier(self) -> Pipeline:
        """Create code quality/complexity classification model"""
        training_data = [
            # High quality
            ("class UserService:\n    def __init__(self, db: Database):\n        self._db = db\n    \n    async def create_user(self, user_data: UserCreate) -> User:\n        validated_data = self._validate_user_data(user_data)\n        return await self._db.users.create(validated_data)", "high_quality"),
            ("def calculate_fibonacci(n: int) -> int:\n    if n <= 1:\n        return n\n    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)", "high_quality"),

            # Medium quality
            ("def process_data(data):\n    result = []\n    for item in data:\n        if item is not None:\n            result.append(item * 2)\n    return result", "medium_quality"),
            ("class Calculator:\n    def add(self, a, b):\n        return a + b\n    def subtract(self, a, b):\n        return a - b", "medium_quality"),

            # Low quality
            ("x=input()\ny=int(x)\nprint(y*2)", "low_quality"),
            ("def func(a,b,c,d,e,f):\n return a+b+c+d+e+f", "low_quality"),
        ]

        texts, labels = zip(*training_data)

        pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(
                max_features=400,
                ngram_range=(1, 2)
            )),
            ('classifier', SVC(kernel='linear', probability=True))
        ])

        def train_model():
            pipeline.fit(texts, labels)
            return pipeline

        return await asyncio.get_event_loop().run_in_executor(self.executor, train_model)

    async def classify_content(self, content: str, title: str = "", description: str = "") -> Dict[str, Any]:
        """
        Classify artifact content using ML models

        Args:
            content: The main content to classify
            title: Optional title for additional context
            description: Optional description for additional context

        Returns:
            Dictionary with classification results
        """
        start_time = datetime.now()

        try:
            # Create cache key
            cache_key = hashlib.md5(f"{content[:1000]}{title}{description}".encode()).hexdigest()

            # Check cache
            if cache_key in self.model_cache:
                cache_entry = self.model_cache[cache_key]
                if datetime.now() - cache_entry['timestamp'] < self.cache_timeout:
                    self.performance_metrics['cache_hits'] += 1
                    return cache_entry['result']

            # Prepare full text for analysis
            full_text = f"{title} {description} {content}".strip()

            # Run classifications in parallel
            classification_tasks = [
                self._classify_language(content),
                self._classify_content_type(full_text),
                self._classify_project_category(full_text),
                self._classify_quality(content),
                self._extract_metadata(content, title, description),
                self._generate_embeddings(full_text)
            ]

            results = await asyncio.gather(*classification_tasks)

            # Combine results
            classification_result = {
                'language': results[0],
                'content_type': results[1],
                'project_category': results[2],
                'quality': results[3],
                'metadata': results[4],
                'embeddings': results[5],
                'timestamp': datetime.now().isoformat(),
                'processing_time_ms': (datetime.now() - start_time).total_seconds() * 1000
            }

            # Update performance metrics
            self.performance_metrics['total_classifications'] += 1
            self.performance_metrics['processing_times'].append(
                classification_result['processing_time_ms']
            )

            # Cache result
            self.model_cache[cache_key] = {
                'result': classification_result,
                'timestamp': datetime.now()
            }

            return classification_result

        except Exception as e:
            logger.error(f"Error in content classification: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def _classify_language(self, content: str) -> Dict[str, Any]:
        """Classify programming language"""
        def classify():
            try:
                prediction = self.models['language'].predict([content])[0]
                probabilities = self.models['language'].predict_proba([content])[0]

                # Get top 3 predictions
                classes = self.models['language'].classes_
                top_indices = np.argsort(probabilities)[::-1][:3]

                return {
                    'predicted': prediction,
                    'confidence': float(max(probabilities)),
                    'top_predictions': [
                        {
                            'language': classes[i],
                            'confidence': float(probabilities[i])
                        } for i in top_indices
                    ]
                }
            except Exception as e:
                return {'error': str(e)}

        return await asyncio.get_event_loop().run_in_executor(self.executor, classify)

    async def _classify_content_type(self, content: str) -> Dict[str, Any]:
        """Classify content type"""
        def classify():
            try:
                prediction = self.models['content_type'].predict([content])[0]
                probabilities = self.models['content_type'].predict_proba([content])[0]

                return {
                    'predicted': prediction,
                    'confidence': float(max(probabilities))
                }
            except Exception as e:
                return {'error': str(e)}

        return await asyncio.get_event_loop().run_in_executor(self.executor, classify)

    async def _classify_project_category(self, content: str) -> Dict[str, Any]:
        """Classify project category"""
        def classify():
            try:
                prediction = self.models['project_category'].predict([content])[0]
                probabilities = self.models['project_category'].predict_proba([content])[0]

                return {
                    'predicted': prediction,
                    'confidence': float(max(probabilities))
                }
            except Exception as e:
                return {'error': str(e)}

        return await asyncio.get_event_loop().run_in_executor(self.executor, classify)

    async def _classify_quality(self, content: str) -> Dict[str, Any]:
        """Classify code quality"""
        def classify():
            try:
                prediction = self.models['quality'].predict([content])[0]
                probabilities = self.models['quality'].predict_proba([content])[0]

                # Calculate additional quality metrics
                lines = content.split('\n')
                metrics = {
                    'line_count': len(lines),
                    'avg_line_length': np.mean([len(line) for line in lines]),
                    'has_comments': any('#' in line or '//' in line or '/*' in content for line in lines),
                    'has_docstrings': '"""' in content or "'''" in content,
                    'complexity_estimate': self._estimate_complexity(content)
                }

                return {
                    'predicted': prediction,
                    'confidence': float(max(probabilities)),
                    'metrics': metrics
                }
            except Exception as e:
                return {'error': str(e)}

        return await asyncio.get_event_loop().run_in_executor(self.executor, classify)

    def _estimate_complexity(self, content: str) -> str:
        """Estimate code complexity based on structural patterns"""
        # Simple complexity estimation
        complexity_indicators = [
            len(re.findall(r'\bif\b|\bwhile\b|\bfor\b', content)),  # Control structures
            len(re.findall(r'\bdef\b|\bclass\b|\bfunction\b', content)),  # Definitions
            len(re.findall(r'\btry\b|\bcatch\b|\bexcept\b', content)),  # Error handling
        ]

        total_complexity = sum(complexity_indicators)

        if total_complexity <= 5:
            return "low"
        elif total_complexity <= 15:
            return "medium"
        else:
            return "high"

    async def _extract_metadata(self, content: str, title: str, description: str) -> Dict[str, Any]:
        """Extract metadata from content"""
        def extract():
            try:
                metadata = {
                    'word_count': len(content.split()),
                    'character_count': len(content),
                    'line_count': len(content.split('\n')),
                    'detected_language': self._detect_natural_language(content + " " + title + " " + description),
                    'sentiment': self._analyze_sentiment(description + " " + title),
                    'keywords': self._extract_keywords(content + " " + title + " " + description),
                    'entities': self._extract_entities(title + " " + description)
                }

                return metadata
            except Exception as e:
                return {'error': str(e)}

        return await asyncio.get_event_loop().run_in_executor(self.executor, extract)

    def _detect_natural_language(self, text: str) -> str:
        """Detect natural language of text"""
        try:
            return detect(text)
        except LangDetectError:
            return "unknown"

    def _analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze sentiment of text"""
        try:
            blob = TextBlob(text)
            return {
                'polarity': blob.sentiment.polarity,
                'subjectivity': blob.sentiment.subjectivity
            }
        except Exception:
            return {'polarity': 0.0, 'subjectivity': 0.0}

    def _extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords from text"""
        try:
            # Simple keyword extraction using TF-IDF
            words = word_tokenize(text.lower())
            words = [word for word in words if word.isalnum() and word not in self.stop_words]

            # Get word frequency
            word_freq = {}
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1

            # Sort by frequency and return top keywords
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            return [word for word, freq in sorted_words[:max_keywords]]

        except Exception:
            return []

    def _extract_entities(self, text: str) -> List[Dict[str, str]]:
        """Extract named entities from text"""
        try:
            if self.nlp_models.get('spacy'):
                doc = self.nlp_models['spacy'](text)
                return [
                    {'text': ent.text, 'label': ent.label_}
                    for ent in doc.ents
                ]
            else:
                return []
        except Exception:
            return []

    async def _generate_embeddings(self, text: str) -> Optional[List[float]]:
        """Generate embeddings for semantic search"""
        def generate():
            try:
                if self.embeddings_model:
                    embeddings = self.embeddings_model.encode([text])
                    return embeddings[0].tolist()
                return None
            except Exception as e:
                logger.warning(f"Error generating embeddings: {e}")
                return None

        return await asyncio.get_event_loop().run_in_executor(self.executor, generate)

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get classifier performance metrics"""
        processing_times = self.performance_metrics['processing_times']

        return {
            'total_classifications': self.performance_metrics['total_classifications'],
            'cache_hits': self.performance_metrics['cache_hits'],
            'cache_hit_rate': (
                self.performance_metrics['cache_hits'] /
                max(self.performance_metrics['total_classifications'], 1)
            ),
            'avg_processing_time_ms': np.mean(processing_times) if processing_times else 0,
            'median_processing_time_ms': np.median(processing_times) if processing_times else 0,
            'models_loaded': list(self.models.keys()),
            'embeddings_available': self.embeddings_model is not None
        }

    async def cleanup(self):
        """Cleanup resources"""
        self.executor.shutdown(wait=True)

# Global instance
ml_classifier = MLContentClassifier()