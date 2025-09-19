"""
Artifacts router for ARTIFACTOR v3.0
Artifact management with v2.0 compatibility
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import List, Optional
import uuid
import hashlib
from datetime import datetime

from ..database import get_database
from ..models import Artifact, User, ArtifactTag
from ..routers.auth import get_current_user
from ..schemas.artifacts import (
    ArtifactResponse, ArtifactCreate, ArtifactUpdate,
    ArtifactSearchRequest, ArtifactListResponse
)

router = APIRouter()

@router.get("/", response_model=ArtifactListResponse)
async def list_artifacts(
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    file_type: Optional[str] = None,
    language: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
):
    """List artifacts with filtering and pagination"""
    try:
        # Build query
        query = select(Artifact).where(
            or_(
                Artifact.owner_id == current_user.id,
                Artifact.is_public == True
            )
        )

        # Apply filters
        if search:
            query = query.where(
                or_(
                    Artifact.title.ilike(f"%{search}%"),
                    Artifact.description.ilike(f"%{search}%"),
                    Artifact.content.ilike(f"%{search}%")
                )
            )

        if file_type:
            query = query.where(Artifact.file_type == file_type)

        if language:
            query = query.where(Artifact.language == language)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination and ordering
        query = query.order_by(Artifact.created_at.desc()).offset(skip).limit(limit)

        # Execute query
        result = await db.execute(query)
        artifacts = result.scalars().all()

        return ArtifactListResponse(
            artifacts=[ArtifactResponse.from_orm(artifact) for artifact in artifacts],
            total=total,
            skip=skip,
            limit=limit
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving artifacts: {str(e)}"
        )

@router.get("/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(
    artifact_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
):
    """Get specific artifact by ID"""
    try:
        query = select(Artifact).where(
            Artifact.id == artifact_id,
            or_(
                Artifact.owner_id == current_user.id,
                Artifact.is_public == True
            )
        )

        result = await db.execute(query)
        artifact = result.scalar_one_or_none()

        if not artifact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Artifact not found"
            )

        # Update view count
        artifact.view_count += 1
        artifact.last_accessed = datetime.utcnow()
        await db.commit()

        return ArtifactResponse.from_orm(artifact)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving artifact: {str(e)}"
        )

@router.post("/", response_model=ArtifactResponse)
async def create_artifact(
    artifact_data: ArtifactCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
):
    """Create new artifact"""
    try:
        # Generate checksum
        checksum = hashlib.sha256(artifact_data.content.encode('utf-8')).hexdigest()

        # Check for duplicate
        existing = await db.execute(
            select(Artifact).where(
                Artifact.checksum == checksum,
                Artifact.owner_id == current_user.id
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Artifact with identical content already exists"
            )

        # Create artifact
        artifact = Artifact(
            title=artifact_data.title,
            description=artifact_data.description,
            content=artifact_data.content,
            file_type=artifact_data.file_type,
            file_extension=artifact_data.file_extension,
            language=artifact_data.language,
            file_size=len(artifact_data.content.encode('utf-8')),
            checksum=checksum,
            owner_id=current_user.id,
            is_public=artifact_data.is_public,
            categories=artifact_data.categories or []
        )

        db.add(artifact)
        await db.commit()
        await db.refresh(artifact)

        # Add tags if provided
        if artifact_data.tags:
            for tag_name in artifact_data.tags:
                tag = ArtifactTag(
                    name=tag_name,
                    artifact_id=artifact.id
                )
                db.add(tag)

            await db.commit()

        return ArtifactResponse.from_orm(artifact)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating artifact: {str(e)}"
        )

@router.put("/{artifact_id}", response_model=ArtifactResponse)
async def update_artifact(
    artifact_id: uuid.UUID,
    artifact_data: ArtifactUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
):
    """Update existing artifact"""
    try:
        # Get artifact
        result = await db.execute(
            select(Artifact).where(
                Artifact.id == artifact_id,
                Artifact.owner_id == current_user.id
            )
        )
        artifact = result.scalar_one_or_none()

        if not artifact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Artifact not found or access denied"
            )

        # Update fields
        update_data = artifact_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(artifact, field):
                setattr(artifact, field, value)

        # Update checksum if content changed
        if 'content' in update_data:
            artifact.checksum = hashlib.sha256(artifact.content.encode('utf-8')).hexdigest()
            artifact.file_size = len(artifact.content.encode('utf-8'))

        artifact.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(artifact)

        return ArtifactResponse.from_orm(artifact)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating artifact: {str(e)}"
        )

@router.delete("/{artifact_id}")
async def delete_artifact(
    artifact_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
):
    """Delete artifact"""
    try:
        # Get artifact
        result = await db.execute(
            select(Artifact).where(
                Artifact.id == artifact_id,
                Artifact.owner_id == current_user.id
            )
        )
        artifact = result.scalar_one_or_none()

        if not artifact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Artifact not found or access denied"
            )

        await db.delete(artifact)
        await db.commit()

        return {"message": "Artifact deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting artifact: {str(e)}"
        )

@router.post("/upload", response_model=ArtifactResponse)
async def upload_artifact(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    is_public: bool = Form(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
):
    """Upload artifact file"""
    try:
        # Read file content
        content = await file.read()
        content_str = content.decode('utf-8')

        # Detect file type and language
        file_extension = Path(file.filename).suffix if file.filename else ""
        file_type, language = _detect_file_type(file.filename, content_str)

        # Create artifact
        artifact_data = ArtifactCreate(
            title=title,
            description=description or f"Uploaded file: {file.filename}",
            content=content_str,
            file_type=file_type,
            file_extension=file_extension,
            language=language,
            is_public=is_public
        )

        return await create_artifact(artifact_data, current_user, db)

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be text-based (binary files not supported)"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file: {str(e)}"
        )

def _detect_file_type(filename: Optional[str], content: str) -> tuple[str, str]:
    """Detect file type and programming language from filename and content"""
    if not filename:
        return ("text", "text")

    # File extension mapping
    extension_map = {
        '.py': ('python', 'python'),
        '.js': ('javascript', 'javascript'),
        '.ts': ('typescript', 'typescript'),
        '.tsx': ('typescript', 'typescript'),
        '.jsx': ('javascript', 'javascript'),
        '.html': ('html', 'html'),
        '.css': ('css', 'css'),
        '.md': ('markdown', 'markdown'),
        '.json': ('json', 'json'),
        '.yaml': ('yaml', 'yaml'),
        '.yml': ('yaml', 'yaml'),
        '.xml': ('xml', 'xml'),
        '.sql': ('sql', 'sql'),
        '.sh': ('shell', 'bash'),
        '.bat': ('batch', 'batch'),
        '.txt': ('text', 'text')
    }

    ext = Path(filename).suffix.lower()
    if ext in extension_map:
        return extension_map[ext]

    # Content-based detection
    content_lower = content.lower()
    if 'import ' in content_lower and ('def ' in content_lower or 'class ' in content_lower):
        return ('python', 'python')
    elif 'function' in content_lower and ('{' in content and '}' in content):
        return ('javascript', 'javascript')
    elif '<!doctype html' in content_lower or '<html' in content_lower:
        return ('html', 'html')

    return ('text', 'text')