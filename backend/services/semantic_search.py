"""
Semantic Search Service for ARTIFACTOR v3.0
Advanced semantic search with natural language queries and vector similarity
"""

import asyncio
import logging
import json
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from datetime import datetime, timedelta
import hashlib
import re

# Vector similarity and search
import faiss
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Database integration
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, func
from sqlalchemy.orm import selectinload

# NLP libraries
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from textblob import TextBlob
import spacy

# Text processing
from fuzzywuzzy import fuzz, process
import re
from collections import defaultdict

# Async processing
from concurrent.futures import ThreadPoolExecutor

# Models
from ..models import Artifact, ArtifactTag, User
from ..database import get_database

logger = logging.getLogger(__name__)

class SemanticSearchService:
    """
    Advanced semantic search service with vector embeddings and NLP
    """

    def __init__(self):
        self.embeddings_model = None
        self.faiss_index = None
        self.artifact_embeddings = {}
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None
        self.nlp_model = None
        self.stop_words = set()
        self.search_cache = {}
        self.cache_timeout = timedelta(minutes=30)
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Search performance metrics
        self.search_metrics = {
            'total_searches': 0,
            'semantic_searches': 0,
            'keyword_searches': 0,
            'hybrid_searches': 0,
            'cache_hits': 0,
            'avg_response_time': 0,
            'search_accuracy_scores': []
        }

        # Index status
        self.index_status = {
            'last_updated': None,
            'total_artifacts': 0,
            'embeddings_count': 0,
            'index_size_mb': 0
        }

    async def initialize(self):
        """Initialize semantic search service"""
        try:
            logger.info("Initializing Semantic Search Service...")

            # Initialize sentence transformer for embeddings
            await self._initialize_embeddings_model()

            # Initialize spaCy model
            await self._initialize_nlp_model()

            # Initialize FAISS index
            await self._initialize_faiss_index()

            # Initialize TF-IDF vectorizer
            await self._initialize_tfidf()

            # Initialize stop words
            self.stop_words = set(stopwords.words('english'))

            logger.info("Semantic Search Service initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing semantic search: {e}")
            raise

    async def _initialize_embeddings_model(self):
        """Initialize sentence transformer model"""
        def load_model():
            try:
                # Use all-MiniLM-L6-v2 for production (good balance of speed/quality)
                return SentenceTransformer('all-MiniLM-L6-v2')
            except Exception as e:
                logger.warning(f"Failed to load sentence transformer: {e}")
                return None

        self.embeddings_model = await asyncio.get_event_loop().run_in_executor(
            self.executor, load_model
        )

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

    async def _initialize_faiss_index(self):
        """Initialize FAISS vector index for similarity search"""
        def create_index():
            try:
                # Create FAISS index for 384-dimensional vectors (all-MiniLM-L6-v2)
                return faiss.IndexFlatIP(384)  # Inner product for cosine similarity
            except Exception as e:
                logger.warning(f"Failed to create FAISS index: {e}")
                return None

        self.faiss_index = await asyncio.get_event_loop().run_in_executor(
            self.executor, create_index
        )

    async def _initialize_tfidf(self):
        """Initialize TF-IDF vectorizer for keyword search"""
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 3),
            stop_words='english',
            lowercase=True,
            token_pattern=r'\b\w+\b'
        )

    async def build_search_index(self, db: AsyncSession):
        """Build search index from all artifacts"""
        try:
            logger.info("Building search index...")

            # Get all artifacts
            query = select(Artifact).options(
                selectinload(Artifact.tags),
                selectinload(Artifact.owner)
            )
            result = await db.execute(query)
            artifacts = result.scalars().all()

            if not artifacts:
                logger.warning("No artifacts found for indexing")
                return

            # Extract texts for indexing
            artifact_texts = []
            artifact_ids = []

            for artifact in artifacts:
                # Combine title, description, content, and tags for search
                tags_text = " ".join([tag.name for tag in artifact.tags])
                full_text = f"{artifact.title} {artifact.description or ''} {artifact.content} {tags_text}"

                artifact_texts.append(full_text)
                artifact_ids.append(str(artifact.id))

            # Build TF-IDF matrix
            await self._build_tfidf_matrix(artifact_texts)

            # Build embeddings and FAISS index
            await self._build_embeddings_index(artifact_texts, artifact_ids)

            # Update index status
            self.index_status.update({
                'last_updated': datetime.now(),
                'total_artifacts': len(artifacts),
                'embeddings_count': len(self.artifact_embeddings)
            })

            logger.info(f"Search index built successfully with {len(artifacts)} artifacts")

        except Exception as e:
            logger.error(f"Error building search index: {e}")
            raise

    async def _build_tfidf_matrix(self, texts: List[str]):
        """Build TF-IDF matrix for keyword search"""
        def build_matrix():
            try:
                self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
                return True
            except Exception as e:
                logger.error(f"Error building TF-IDF matrix: {e}")
                return False

        await asyncio.get_event_loop().run_in_executor(self.executor, build_matrix)

    async def _build_embeddings_index(self, texts: List[str], artifact_ids: List[str]):
        """Build embeddings and FAISS index"""
        def build_embeddings():
            try:
                if not self.embeddings_model or not self.faiss_index:
                    return False

                # Generate embeddings
                embeddings = self.embeddings_model.encode(texts, show_progress_bar=True)

                # Normalize embeddings for cosine similarity
                faiss.normalize_L2(embeddings)

                # Add to FAISS index
                self.faiss_index.add(embeddings)

                # Store embeddings mapping
                for i, artifact_id in enumerate(artifact_ids):
                    self.artifact_embeddings[artifact_id] = embeddings[i]

                return True

            except Exception as e:
                logger.error(f"Error building embeddings index: {e}")
                return False

        await asyncio.get_event_loop().run_in_executor(self.executor, build_embeddings)

    async def search(
        self,
        query: str,
        db: AsyncSession,
        user_id: Optional[str] = None,
        search_type: str = "hybrid",
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform semantic search on artifacts

        Args:
            query: Search query (natural language)
            db: Database session
            user_id: User ID for permission filtering
            search_type: "semantic", "keyword", or "hybrid"
            limit: Maximum number of results
            filters: Additional filters (file_type, language, etc.)

        Returns:
            Search results with relevance scores
        """
        start_time = datetime.now()

        try:
            # Check cache
            cache_key = hashlib.md5(
                f"{query}{user_id}{search_type}{limit}{str(filters)}".encode()
            ).hexdigest()

            if cache_key in self.search_cache:
                cache_entry = self.search_cache[cache_key]
                if datetime.now() - cache_entry['timestamp'] < self.cache_timeout:
                    self.search_metrics['cache_hits'] += 1
                    return cache_entry['result']

            # Preprocess query
            processed_query = await self._preprocess_query(query)

            # Perform search based on type
            if search_type == "semantic":
                results = await self._semantic_search(processed_query, db, user_id, limit, filters)
                self.search_metrics['semantic_searches'] += 1
            elif search_type == "keyword":
                results = await self._keyword_search(processed_query, db, user_id, limit, filters)
                self.search_metrics['keyword_searches'] += 1
            else:  # hybrid
                results = await self._hybrid_search(processed_query, db, user_id, limit, filters)
                self.search_metrics['hybrid_searches'] += 1

            # Calculate response time
            response_time = (datetime.now() - start_time).total_seconds() * 1000

            # Prepare final result
            search_result = {
                'query': query,
                'processed_query': processed_query,
                'search_type': search_type,
                'results': results,
                'total_results': len(results),
                'response_time_ms': response_time,
                'timestamp': datetime.now().isoformat()
            }

            # Update metrics
            self.search_metrics['total_searches'] += 1
            self.search_metrics['avg_response_time'] = (
                (self.search_metrics['avg_response_time'] * (self.search_metrics['total_searches'] - 1) + response_time) /
                self.search_metrics['total_searches']
            )

            # Cache result
            self.search_cache[cache_key] = {
                'result': search_result,
                'timestamp': datetime.now()
            }

            return search_result

        except Exception as e:
            logger.error(f"Error in search: {e}")
            return {
                'error': str(e),
                'query': query,
                'timestamp': datetime.now().isoformat()
            }

    async def _preprocess_query(self, query: str) -> Dict[str, Any]:
        """Preprocess search query"""
        def preprocess():
            try:
                # Clean query
                cleaned_query = re.sub(r'[^\w\s]', ' ', query.lower()).strip()

                # Extract keywords
                keywords = word_tokenize(cleaned_query)
                keywords = [word for word in keywords if word not in self.stop_words and len(word) > 2]

                # Analyze intent
                intent = self._analyze_query_intent(query)

                # Extract entities if spaCy is available
                entities = []
                if self.nlp_model:
                    doc = self.nlp_model(query)
                    entities = [(ent.text, ent.label_) for ent in doc.ents]

                return {
                    'original': query,
                    'cleaned': cleaned_query,
                    'keywords': keywords,
                    'intent': intent,
                    'entities': entities
                }

            except Exception as e:
                logger.warning(f"Error preprocessing query: {e}")
                return {
                    'original': query,
                    'cleaned': query.lower(),
                    'keywords': query.split(),
                    'intent': 'general',
                    'entities': []
                }

        return await asyncio.get_event_loop().run_in_executor(self.executor, preprocess)

    def _analyze_query_intent(self, query: str) -> str:
        """Analyze query intent"""
        query_lower = query.lower()

        # Intent patterns
        if any(word in query_lower for word in ['how to', 'tutorial', 'guide', 'example']):
            return 'learning'
        elif any(word in query_lower for word in ['api', 'function', 'method', 'class']):
            return 'code_reference'
        elif any(word in query_lower for word in ['bug', 'error', 'fix', 'debug']):
            return 'debugging'
        elif any(word in query_lower for word in ['test', 'testing', 'unit test']):
            return 'testing'
        elif any(word in query_lower for word in ['config', 'setup', 'install']):
            return 'configuration'
        else:
            return 'general'

    async def _semantic_search(
        self,
        processed_query: Dict[str, Any],
        db: AsyncSession,
        user_id: Optional[str],
        limit: int,
        filters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Perform semantic search using embeddings"""
        if not self.embeddings_model or not self.faiss_index:
            return []

        def search_embeddings():
            try:
                # Generate query embedding
                query_embedding = self.embeddings_model.encode([processed_query['cleaned']])
                faiss.normalize_L2(query_embedding)

                # Search FAISS index
                scores, indices = self.faiss_index.search(query_embedding, limit * 2)  # Get more for filtering

                return scores[0], indices[0]

            except Exception as e:
                logger.error(f"Error in semantic search: {e}")
                return [], []

        scores, indices = await asyncio.get_event_loop().run_in_executor(
            self.executor, search_embeddings
        )

        if not len(scores):
            return []

        # Get artifact IDs from indices
        artifact_ids = []
        artifact_scores = []

        for i, idx in enumerate(indices):
            if idx < len(list(self.artifact_embeddings.keys())):
                artifact_id = list(self.artifact_embeddings.keys())[idx]
                artifact_ids.append(artifact_id)
                artifact_scores.append(float(scores[i]))

        # Query database for artifacts
        results = await self._query_artifacts_by_ids(
            artifact_ids, artifact_scores, db, user_id, limit, filters
        )

        return results

    async def _keyword_search(
        self,
        processed_query: Dict[str, Any],
        db: AsyncSession,
        user_id: Optional[str],
        limit: int,
        filters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Perform keyword-based search using TF-IDF"""
        if not self.tfidf_vectorizer or self.tfidf_matrix is None:
            return []

        def search_tfidf():
            try:
                # Transform query
                query_vector = self.tfidf_vectorizer.transform([processed_query['cleaned']])

                # Calculate similarity
                similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()

                # Get top results
                top_indices = np.argsort(similarities)[::-1][:limit * 2]
                top_scores = similarities[top_indices]

                return top_scores, top_indices

            except Exception as e:
                logger.error(f"Error in keyword search: {e}")
                return [], []

        scores, indices = await asyncio.get_event_loop().run_in_executor(
            self.executor, search_tfidf
        )

        if not len(scores):
            return []

        # Get artifact IDs (assuming same order as when TF-IDF was built)
        artifact_ids = list(self.artifact_embeddings.keys())

        result_artifacts = []
        result_scores = []

        for i, idx in enumerate(indices):
            if idx < len(artifact_ids) and scores[i] > 0.1:  # Minimum relevance threshold
                result_artifacts.append(artifact_ids[idx])
                result_scores.append(float(scores[i]))

        # Query database for artifacts
        results = await self._query_artifacts_by_ids(
            result_artifacts, result_scores, db, user_id, limit, filters
        )

        return results

    async def _hybrid_search(
        self,
        processed_query: Dict[str, Any],
        db: AsyncSession,
        user_id: Optional[str],
        limit: int,
        filters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Perform hybrid search combining semantic and keyword approaches"""
        # Run both searches
        semantic_results = await self._semantic_search(
            processed_query, db, user_id, limit, filters
        )
        keyword_results = await self._keyword_search(
            processed_query, db, user_id, limit, filters
        )

        # Combine and re-rank results
        combined_results = self._combine_search_results(
            semantic_results, keyword_results, processed_query
        )

        return combined_results[:limit]

    def _combine_search_results(
        self,
        semantic_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]],
        processed_query: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Combine and re-rank search results from different methods"""
        # Create combined results dict
        combined = {}

        # Add semantic results with weight
        for result in semantic_results:
            artifact_id = result['id']
            combined[artifact_id] = result.copy()
            combined[artifact_id]['semantic_score'] = result['relevance_score']
            combined[artifact_id]['keyword_score'] = 0.0

        # Add keyword results with weight
        for result in keyword_results:
            artifact_id = result['id']
            if artifact_id in combined:
                combined[artifact_id]['keyword_score'] = result['relevance_score']
            else:
                combined[artifact_id] = result.copy()
                combined[artifact_id]['semantic_score'] = 0.0
                combined[artifact_id]['keyword_score'] = result['relevance_score']

        # Calculate hybrid score
        for artifact_id, result in combined.items():
            semantic_weight = 0.6
            keyword_weight = 0.4

            # Adjust weights based on query intent
            if processed_query['intent'] == 'code_reference':
                semantic_weight = 0.7
                keyword_weight = 0.3
            elif processed_query['intent'] == 'learning':
                semantic_weight = 0.8
                keyword_weight = 0.2

            hybrid_score = (
                semantic_weight * result['semantic_score'] +
                keyword_weight * result['keyword_score']
            )

            result['relevance_score'] = hybrid_score
            result['search_method'] = 'hybrid'

        # Sort by hybrid score
        sorted_results = sorted(
            combined.values(),
            key=lambda x: x['relevance_score'],
            reverse=True
        )

        return sorted_results

    async def _query_artifacts_by_ids(
        self,
        artifact_ids: List[str],
        scores: List[float],
        db: AsyncSession,
        user_id: Optional[str],
        limit: int,
        filters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Query artifacts by IDs and return formatted results"""
        try:
            # Build query
            query = select(Artifact).options(
                selectinload(Artifact.tags),
                selectinload(Artifact.owner)
            ).where(Artifact.id.in_(artifact_ids))

            # Add permission filter
            if user_id:
                query = query.where(
                    (Artifact.owner_id == user_id) | (Artifact.is_public == True)
                )
            else:
                query = query.where(Artifact.is_public == True)

            # Add additional filters
            if filters:
                if filters.get('file_type'):
                    query = query.where(Artifact.file_type == filters['file_type'])
                if filters.get('language'):
                    query = query.where(Artifact.language == filters['language'])

            # Execute query
            result = await db.execute(query)
            artifacts = result.scalars().all()

            # Format results
            formatted_results = []
            artifact_score_map = dict(zip(artifact_ids, scores))

            for artifact in artifacts:
                artifact_id = str(artifact.id)
                relevance_score = artifact_score_map.get(artifact_id, 0.0)

                formatted_result = {
                    'id': artifact_id,
                    'title': artifact.title,
                    'description': artifact.description,
                    'file_type': artifact.file_type,
                    'language': artifact.language,
                    'owner': artifact.owner.username if artifact.owner else None,
                    'created_at': artifact.created_at.isoformat(),
                    'tags': [tag.name for tag in artifact.tags],
                    'relevance_score': relevance_score,
                    'view_count': artifact.view_count,
                    'download_count': artifact.download_count
                }

                formatted_results.append(formatted_result)

            # Sort by relevance score
            formatted_results.sort(key=lambda x: x['relevance_score'], reverse=True)

            return formatted_results[:limit]

        except Exception as e:
            logger.error(f"Error querying artifacts: {e}")
            return []

    async def suggest_related_artifacts(
        self,
        artifact_id: str,
        db: AsyncSession,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Suggest related artifacts based on content similarity"""
        try:
            if artifact_id not in self.artifact_embeddings:
                return []

            # Get artifact embedding
            artifact_embedding = self.artifact_embeddings[artifact_id].reshape(1, -1)

            # Search for similar artifacts
            scores, indices = self.faiss_index.search(artifact_embedding, limit + 1)  # +1 to exclude self

            # Remove the artifact itself and get related ones
            related_ids = []
            related_scores = []

            artifact_ids_list = list(self.artifact_embeddings.keys())

            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx < len(artifact_ids_list):
                    related_id = artifact_ids_list[idx]
                    if related_id != artifact_id:  # Exclude self
                        related_ids.append(related_id)
                        related_scores.append(float(score))

            # Query database for related artifacts
            results = await self._query_artifacts_by_ids(
                related_ids[:limit], related_scores[:limit], db, None, limit, None
            )

            return results

        except Exception as e:
            logger.error(f"Error finding related artifacts: {e}")
            return []

    async def get_search_analytics(self) -> Dict[str, Any]:
        """Get search analytics and performance metrics"""
        return {
            'metrics': self.search_metrics.copy(),
            'index_status': self.index_status.copy(),
            'cache_stats': {
                'cache_size': len(self.search_cache),
                'cache_timeout_minutes': self.cache_timeout.total_seconds() / 60
            }
        }

    async def cleanup(self):
        """Cleanup resources"""
        self.executor.shutdown(wait=True)

# Global instance
semantic_search_service = SemanticSearchService()