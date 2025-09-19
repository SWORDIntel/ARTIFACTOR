"""
Pydantic schemas for artifact endpoints
"""

from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

class ArtifactBase(BaseModel):
    """Base artifact schema"""
    title: str
    description: Optional[str] = None
    content: str
    file_type: str
    file_extension: Optional[str] = None
    language: Optional[str] = None
    is_public: bool = False
    categories: Optional[List[str]] = None

    @validator('title')
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        if len(v.strip()) > 255:
            raise ValueError('Title must be less than 255 characters')
        return v.strip()

    @validator('content')
    def validate_content(cls, v):
        if not v.strip():
            raise ValueError('Content cannot be empty')
        if len(v) > 10 * 1024 * 1024:  # 10MB limit
            raise ValueError('Content must be less than 10MB')
        return v

class ArtifactCreate(ArtifactBase):
    """Schema for creating artifacts"""
    tags: Optional[List[str]] = None

    @validator('tags')
    def validate_tags(cls, v):
        if v:
            if len(v) > 20:
                raise ValueError('Maximum 20 tags allowed')
            for tag in v:
                if len(tag.strip()) > 50:
                    raise ValueError('Tag must be less than 50 characters')
        return v

class ArtifactUpdate(BaseModel):
    """Schema for updating artifacts"""
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    is_public: Optional[bool] = None
    categories: Optional[List[str]] = None

class ArtifactResponse(BaseModel):
    """Schema for artifact responses"""
    id: uuid.UUID
    title: str
    description: Optional[str] = None
    content: str
    file_type: str
    file_extension: Optional[str] = None
    language: Optional[str] = None
    file_size: int
    checksum: str
    is_public: bool
    is_archived: bool
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    downloaded_at: Optional[datetime] = None
    download_count: int
    view_count: int
    last_accessed: Optional[datetime] = None
    categories: List[str]
    processing_status: str
    agent_metadata: Dict[str, Any]

    class Config:
        from_attributes = True

class ArtifactListResponse(BaseModel):
    """Schema for artifact list responses"""
    artifacts: List[ArtifactResponse]
    total: int
    skip: int
    limit: int

class ArtifactSearchRequest(BaseModel):
    """Schema for artifact search requests"""
    query: str
    file_types: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    public_only: bool = False

    @validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError('Search query cannot be empty')
        if len(v.strip()) > 500:
            raise ValueError('Search query must be less than 500 characters')
        return v.strip()