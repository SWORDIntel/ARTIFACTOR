"""
Database models for ARTIFACTOR v3.0
SQLAlchemy models with PostgreSQL-specific features
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Index, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from .database import Base

# Import collaboration models
from .models.collaboration import *

class User(Base):
    """User model with authentication and authorization"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))

    # Relationships
    artifacts = relationship("Artifact", back_populates="owner", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="author", cascade="all, delete-orphan")
    user_sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")

    # User preferences and settings
    preferences = Column(JSON, default=dict)
    agent_settings = Column(JSON, default=dict)

    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"

class Artifact(Base):
    """Artifact model for storing Claude.ai artifacts and files"""
    __tablename__ = "artifacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    content = Column(Text, nullable=False)
    file_type = Column(String(50), nullable=False, index=True)
    file_extension = Column(String(10))
    language = Column(String(50), index=True)

    # Metadata
    original_url = Column(String(500))
    claude_conversation_id = Column(String(255), index=True)
    artifact_identifier = Column(String(255), index=True)

    # File information
    file_size = Column(Integer)
    file_path = Column(String(500))
    checksum = Column(String(64))  # SHA-256 hash

    # Status and visibility
    is_public = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    status = Column(String(20), default="active", index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    downloaded_at = Column(DateTime(timezone=True))

    # Relationships
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="artifacts")
    comments = relationship("Comment", back_populates="artifact", cascade="all, delete-orphan")
    tags = relationship("ArtifactTag", back_populates="artifact", cascade="all, delete-orphan")
    ml_classifications = relationship("MLClassification", back_populates="artifact", cascade="all, delete-orphan")
    embedding = relationship("ArtifactEmbedding", back_populates="artifact", uselist=False, cascade="all, delete-orphan")

    # Full-text search and categorization
    search_vector = Column(Text)  # PostgreSQL full-text search
    categories = Column(ARRAY(String), default=list)

    # Agent coordination metadata
    processing_status = Column(String(50), default="pending")
    agent_metadata = Column(JSON, default=dict)
    validation_results = Column(JSON, default=dict)

    # Performance and analytics
    download_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    last_accessed = Column(DateTime(timezone=True))

    def __repr__(self):
        return f"<Artifact(title='{self.title}', type='{self.file_type}')>"

class Comment(Base):
    """Comments and collaboration on artifacts"""
    __tablename__ = "comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_resolved = Column(Boolean, default=False)

    # Relationships
    artifact_id = Column(UUID(as_uuid=True), ForeignKey("artifacts.id"), nullable=False)
    artifact = relationship("Artifact", back_populates="comments")
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    author = relationship("User", back_populates="comments")

    # Threading support
    parent_id = Column(UUID(as_uuid=True), ForeignKey("comments.id"))
    parent = relationship("Comment", remote_side=[id])

    def __repr__(self):
        return f"<Comment(artifact_id='{self.artifact_id}', author='{self.author.username}')>"

class ArtifactTag(Base):
    """Tags for artifact categorization"""
    __tablename__ = "artifact_tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), nullable=False, index=True)
    color = Column(String(7), default="#007bff")  # Hex color
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    artifact_id = Column(UUID(as_uuid=True), ForeignKey("artifacts.id"), nullable=False)
    artifact = relationship("Artifact", back_populates="tags")

    def __repr__(self):
        return f"<ArtifactTag(name='{self.name}')>"

class UserSession(Base):
    """User session management"""
    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

    # Session metadata
    ip_address = Column(String(45))  # IPv6 support
    user_agent = Column(Text)
    device_info = Column(JSON, default=dict)

    # Relationships
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="user_sessions")

    def __repr__(self):
        return f"<UserSession(user='{self.user.username}', expires='{self.expires_at}')>"

class Plugin(Base):
    """Plugin system for extensibility"""
    __tablename__ = "plugins"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    version = Column(String(20), nullable=False)
    description = Column(Text)
    author = Column(String(100))

    # Plugin configuration
    config_schema = Column(JSON, default=dict)
    default_config = Column(JSON, default=dict)
    is_enabled = Column(Boolean, default=False)
    is_system_plugin = Column(Boolean, default=False)

    # Installation info
    installed_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    install_path = Column(String(500))

    # Dependencies and requirements
    dependencies = Column(ARRAY(String), default=list)
    requirements = Column(JSON, default=dict)

    def __repr__(self):
        return f"<Plugin(name='{self.name}', version='{self.version}')>"

class PerformanceMetric(Base):
    """Performance monitoring and analytics"""
    __tablename__ = "performance_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(String(255), nullable=False)
    metric_type = Column(String(50), nullable=False)  # counter, gauge, histogram
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Context and metadata
    component = Column(String(100), index=True)  # backend, frontend, agent_bridge
    tags = Column(JSON, default=dict)
    additional_data = Column(JSON, default=dict)

    def __repr__(self):
        return f"<PerformanceMetric(name='{self.metric_name}', value='{self.metric_value}')>"

class AgentExecution(Base):
    """Agent coordination and execution tracking"""
    __tablename__ = "agent_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_name = Column(String(100), nullable=False, index=True)
    task_type = Column(String(100), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="pending", index=True)

    # Execution details
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    execution_time = Column(Integer)  # milliseconds

    # Input/Output
    input_data = Column(JSON, default=dict)
    output_data = Column(JSON, default=dict)
    error_details = Column(JSON, default=dict)

    # Relationships
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    artifact_id = Column(UUID(as_uuid=True), ForeignKey("artifacts.id"))

    # v2.0 compatibility tracking
    v2_compatibility = Column(Boolean, default=True)
    coordination_overhead = Column(Integer)  # Track 99.7% optimization

    def __repr__(self):
        return f"<AgentExecution(agent='{self.agent_name}', status='{self.status}')>"

class MLClassification(Base):
    """ML classification results for artifacts"""
    __tablename__ = "ml_classifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    artifact_id = Column(UUID(as_uuid=True), ForeignKey("artifacts.id"), nullable=False, index=True)

    # Classification results
    predicted_language = Column(String(50), index=True)
    language_confidence = Column(Float)
    content_type = Column(String(50), index=True)
    content_type_confidence = Column(Float)
    project_category = Column(String(100), index=True)
    project_category_confidence = Column(Float)
    quality_assessment = Column(String(20))
    quality_confidence = Column(Float)

    # Processing metadata
    classification_version = Column(String(20), default="1.0")
    processing_time_ms = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Full classification data
    full_results = Column(JSON, default=dict)

    # Relationships
    artifact = relationship("Artifact", back_populates="ml_classifications")

    def __repr__(self):
        return f"<MLClassification(artifact='{self.artifact_id}', language='{self.predicted_language}')>"

class ArtifactEmbedding(Base):
    """Vector embeddings for semantic search"""
    __tablename__ = "artifact_embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    artifact_id = Column(UUID(as_uuid=True), ForeignKey("artifacts.id"), nullable=False, unique=True, index=True)

    # Embedding data
    embedding_vector = Column(ARRAY(Float), nullable=False)  # 384-dimensional vector
    embedding_model = Column(String(100), default="all-MiniLM-L6-v2")
    embedding_version = Column(String(20), default="1.0")

    # Metadata for embedding generation
    content_hash = Column(String(64), index=True)  # SHA-256 of content used
    text_processed = Column(Text)  # Preprocessed text used for embedding
    processing_time_ms = Column(Integer)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    artifact = relationship("Artifact", back_populates="embedding")

    def __repr__(self):
        return f"<ArtifactEmbedding(artifact='{self.artifact_id}', model='{self.embedding_model}')>"

class SearchQuery(Base):
    """Search query logging and analytics"""
    __tablename__ = "search_queries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_text = Column(Text, nullable=False, index=True)
    search_type = Column(String(20), nullable=False, index=True)  # semantic, keyword, hybrid

    # User and session info
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    session_id = Column(String(255), index=True)
    ip_address = Column(String(45))

    # Query processing
    processed_query = Column(JSON, default=dict)
    filters_applied = Column(JSON, default=dict)
    results_count = Column(Integer, default=0)
    response_time_ms = Column(Integer)

    # Results interaction
    clicked_results = Column(ARRAY(String))  # Artifact IDs that were clicked
    no_results = Column(Boolean, default=False)
    user_satisfied = Column(Boolean)  # User feedback if available

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<SearchQuery(query='{self.query_text[:50]}...', type='{self.search_type}')>"

class MLModelMetrics(Base):
    """ML model performance metrics and monitoring"""
    __tablename__ = "ml_model_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name = Column(String(100), nullable=False, index=True)
    model_version = Column(String(20), nullable=False)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)

    # Context
    evaluation_context = Column(JSON, default=dict)  # Test set info, conditions, etc.
    sample_size = Column(Integer)

    # Timestamps
    measured_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self):
        return f"<MLModelMetrics(model='{self.model_name}', metric='{self.metric_name}', value={self.metric_value})>"

class TagSuggestion(Base):
    """Smart tag suggestions and user feedback"""
    __tablename__ = "tag_suggestions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    artifact_id = Column(UUID(as_uuid=True), ForeignKey("artifacts.id"), nullable=False, index=True)

    # Suggestion details
    suggested_tag = Column(String(100), nullable=False, index=True)
    confidence_score = Column(Float, nullable=False)
    suggestion_source = Column(String(50), nullable=False)  # technology_analysis, nlp, etc.

    # User feedback
    user_accepted = Column(Boolean)  # Did user accept the suggestion?
    user_feedback = Column(String(500))  # Optional feedback
    feedback_timestamp = Column(DateTime(timezone=True))

    # Suggestion metadata
    suggestion_context = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    artifact = relationship("Artifact")

    def __repr__(self):
        return f"<TagSuggestion(tag='{self.suggested_tag}', confidence={self.confidence_score})>"

# Database indexes for performance
Index('idx_artifacts_search', Artifact.title, Artifact.description)
Index('idx_artifacts_created', Artifact.created_at.desc())
Index('idx_artifacts_owner_created', Artifact.owner_id, Artifact.created_at.desc())
Index('idx_comments_artifact_created', Comment.artifact_id, Comment.created_at.desc())
Index('idx_performance_metrics_time', PerformanceMetric.timestamp.desc())
Index('idx_agent_executions_status_time', AgentExecution.status, AgentExecution.started_at.desc())

# ML-specific indexes for performance optimization
Index('idx_ml_classifications_artifact', MLClassification.artifact_id)
Index('idx_ml_classifications_language', MLClassification.predicted_language)
Index('idx_ml_classifications_content_type', MLClassification.content_type)
Index('idx_ml_classifications_category', MLClassification.project_category)
Index('idx_artifact_embeddings_artifact', ArtifactEmbedding.artifact_id)
Index('idx_artifact_embeddings_hash', ArtifactEmbedding.content_hash)
Index('idx_search_queries_user_time', SearchQuery.user_id, SearchQuery.created_at.desc())
Index('idx_search_queries_text', SearchQuery.query_text)
Index('idx_search_queries_type_time', SearchQuery.search_type, SearchQuery.created_at.desc())
Index('idx_ml_model_metrics_model_time', MLModelMetrics.model_name, MLModelMetrics.measured_at.desc())
Index('idx_tag_suggestions_artifact', TagSuggestion.artifact_id)
Index('idx_tag_suggestions_tag', TagSuggestion.suggested_tag)
Index('idx_tag_suggestions_feedback', TagSuggestion.user_accepted)