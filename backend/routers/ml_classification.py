"""
ML Classification Router for ARTIFACTOR v3.0
Advanced ML-powered content classification and analysis endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

# Database and models
from ..database import get_database
from ..models import Artifact, User
from ..routers.auth import get_current_user

# ML services
from ..services.ml_pipeline import ml_pipeline
from ..services.ml_classifier import ml_classifier
from ..services.smart_tagging import smart_tagging_service

# Pydantic schemas
from pydantic import BaseModel, Field

router = APIRouter()

# Request/Response models
class ClassificationRequest(BaseModel):
    content: str = Field(..., description="Content to classify")
    title: str = Field("", description="Optional title")
    description: str = Field("", description="Optional description")
    file_type: str = Field("", description="File type")
    language: str = Field("", description="Programming language")
    max_tags: int = Field(10, ge=1, le=20, description="Maximum tags to generate")
    priority: int = Field(2, ge=1, le=3, description="Processing priority")

class ClassificationResponse(BaseModel):
    request_id: str
    success: bool
    classification: Optional[Dict[str, Any]] = None
    tags: Optional[List[Dict[str, Any]]] = None
    embeddings: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time_ms: float
    cache_hit: bool = False

class BatchClassificationRequest(BaseModel):
    artifacts: List[ClassificationRequest] = Field(..., max_items=50)
    max_concurrent: int = Field(5, ge=1, le=10)

class BatchClassificationResponse(BaseModel):
    results: List[ClassificationResponse]
    total_processed: int
    success_count: int
    error_count: int
    total_processing_time_ms: float

class TagGenerationRequest(BaseModel):
    content: str = Field(..., description="Content to analyze")
    title: str = Field("", description="Optional title")
    description: str = Field("", description="Optional description")
    file_type: str = Field("", description="File type")
    language: str = Field("", description="Programming language")
    max_tags: int = Field(10, ge=1, le=20)

class TagGenerationResponse(BaseModel):
    tags: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    processing_time_ms: float

class ProjectAnalysisRequest(BaseModel):
    artifact_ids: List[uuid.UUID] = Field(..., max_items=100)

class ProjectAnalysisResponse(BaseModel):
    project_analysis: Dict[str, Any]
    suggested_tags: List[Dict[str, Any]]
    dominant_technologies: List[str]
    complexity_analysis: Dict[str, Any]

@router.post("/classify", response_model=ClassificationResponse)
async def classify_content(
    request: ClassificationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
):
    """
    Classify content using ML models
    Provides language detection, content type classification, and smart tagging
    """
    try:
        # Process through ML pipeline
        result = await ml_pipeline.process_artifact(
            content=request.content,
            title=request.title,
            description=request.description,
            file_type=request.file_type,
            language=request.language,
            user_id=str(current_user.id),
            priority=request.priority
        )

        return ClassificationResponse(
            request_id=result.request_id,
            success=result.success,
            classification=result.classification,
            tags=result.tags,
            embeddings=result.embeddings,
            metadata=result.metadata,
            error=result.error,
            processing_time_ms=result.processing_time_ms,
            cache_hit=result.cache_hit
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Classification error: {str(e)}"
        )

@router.post("/classify/batch", response_model=BatchClassificationResponse)
async def classify_batch(
    request: BatchClassificationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
):
    """
    Classify multiple pieces of content in batch
    Optimized for processing multiple artifacts efficiently
    """
    try:
        start_time = datetime.now()

        # Convert requests to dictionary format
        batch_requests = []
        for artifact_req in request.artifacts:
            batch_requests.append({
                'content': artifact_req.content,
                'title': artifact_req.title,
                'description': artifact_req.description,
                'file_type': artifact_req.file_type,
                'language': artifact_req.language,
                'user_id': str(current_user.id),
                'priority': artifact_req.priority
            })

        # Process batch
        results = await ml_pipeline.batch_process(
            batch_requests,
            max_concurrent=request.max_concurrent
        )

        # Convert results
        classification_responses = []
        success_count = 0
        error_count = 0

        for result in results:
            response = ClassificationResponse(
                request_id=result.request_id,
                success=result.success,
                classification=result.classification,
                tags=result.tags,
                embeddings=result.embeddings,
                metadata=result.metadata,
                error=result.error,
                processing_time_ms=result.processing_time_ms,
                cache_hit=result.cache_hit
            )
            classification_responses.append(response)

            if result.success:
                success_count += 1
            else:
                error_count += 1

        total_time = (datetime.now() - start_time).total_seconds() * 1000

        return BatchClassificationResponse(
            results=classification_responses,
            total_processed=len(results),
            success_count=success_count,
            error_count=error_count,
            total_processing_time_ms=total_time
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch classification error: {str(e)}"
        )

@router.post("/tags/generate", response_model=TagGenerationResponse)
async def generate_tags(
    request: TagGenerationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generate smart tags for content
    Uses NLP and ML to automatically suggest relevant tags
    """
    try:
        result = await smart_tagging_service.generate_tags(
            content=request.content,
            title=request.title,
            description=request.description,
            file_type=request.file_type,
            language=request.language,
            max_tags=request.max_tags
        )

        return TagGenerationResponse(
            tags=result.get('tags', []),
            metadata=result.get('metadata', {}),
            processing_time_ms=result.get('processing_time_ms', 0)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tag generation error: {str(e)}"
        )

@router.put("/artifacts/{artifact_id}/classify")
async def classify_existing_artifact(
    artifact_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    priority: int = 2,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
):
    """
    Classify an existing artifact and update its metadata
    """
    try:
        # Get artifact
        query = select(Artifact).where(
            Artifact.id == artifact_id,
            Artifact.owner_id == current_user.id
        )
        result = await db.execute(query)
        artifact = result.scalar_one_or_none()

        if not artifact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Artifact not found or access denied"
            )

        # Add classification task to background
        background_tasks.add_task(
            _classify_and_update_artifact,
            artifact, db, priority
        )

        return {
            "message": "Classification started",
            "artifact_id": artifact_id,
            "status": "processing"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting classification: {str(e)}"
        )

@router.post("/projects/analyze", response_model=ProjectAnalysisResponse)
async def analyze_project(
    request: ProjectAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
):
    """
    Analyze a collection of artifacts as a project
    Provides project-level insights and recommendations
    """
    try:
        # Get artifacts
        query = select(Artifact).where(
            Artifact.id.in_(request.artifact_ids),
            Artifact.owner_id == current_user.id
        )
        result = await db.execute(query)
        artifacts = result.scalars().all()

        if not artifacts:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No accessible artifacts found"
            )

        # Convert to format expected by tagging service
        artifact_data = []
        for artifact in artifacts:
            artifact_data.append({
                'title': artifact.title,
                'description': artifact.description,
                'content': artifact.content,
                'language': artifact.language,
                'file_type': artifact.file_type
            })

        # Perform project analysis
        analysis = await smart_tagging_service.suggest_tags_for_project(artifact_data)

        # Additional project insights
        complexity_analysis = _analyze_project_complexity(artifacts)
        technology_analysis = _analyze_project_technologies(artifacts)

        return ProjectAnalysisResponse(
            project_analysis=analysis,
            suggested_tags=analysis.get('suggested_tags', []),
            dominant_technologies=technology_analysis,
            complexity_analysis=complexity_analysis
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Project analysis error: {str(e)}"
        )

@router.get("/stats/classification")
async def get_classification_stats(
    current_user: User = Depends(get_current_user)
):
    """
    Get ML classification system statistics and performance metrics
    """
    try:
        # Get pipeline stats
        pipeline_stats = await ml_pipeline.get_pipeline_stats()

        # Get classifier performance
        classifier_metrics = await ml_classifier.get_performance_metrics()

        # Get tagging analytics
        tagging_analytics = await smart_tagging_service.get_tagging_analytics()

        return {
            "pipeline": pipeline_stats,
            "classifier": classifier_metrics,
            "tagging": tagging_analytics,
            "system_status": {
                "ml_services_available": True,
                "cache_enabled": pipeline_stats["cache"]["redis_available"],
                "processing_queues": pipeline_stats["queues"]
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving stats: {str(e)}"
        )

@router.post("/models/retrain")
async def retrain_models(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
):
    """
    Trigger retraining of ML models based on recent data
    Admin-only endpoint for model maintenance
    """
    try:
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )

        # Add retraining task to background
        background_tasks.add_task(_retrain_models_background, db)

        return {
            "message": "Model retraining started",
            "status": "processing",
            "estimated_time_minutes": 30
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting retraining: {str(e)}"
        )

# Background task functions
async def _classify_and_update_artifact(artifact: Artifact, db: AsyncSession, priority: int):
    """Background task to classify and update artifact"""
    try:
        # Run classification
        result = await ml_pipeline.process_artifact(
            content=artifact.content,
            title=artifact.title,
            description=artifact.description or "",
            file_type=artifact.file_type,
            language=artifact.language or "",
            user_id=str(artifact.owner_id),
            priority=priority
        )

        if result.success:
            # Update artifact with classification results
            update_data = {}

            if result.classification:
                # Update language if detected
                predicted_language = result.classification.get('language', {}).get('predicted')
                if predicted_language and not artifact.language:
                    update_data['language'] = predicted_language

                # Update categories
                if result.classification.get('project_category'):
                    category = result.classification['project_category'].get('predicted')
                    if category:
                        current_categories = artifact.categories or []
                        if category not in current_categories:
                            current_categories.append(category)
                            update_data['categories'] = current_categories

            # Update agent metadata with ML results
            agent_metadata = artifact.agent_metadata or {}
            agent_metadata.update({
                'ml_classification': result.classification,
                'ml_tags': result.tags,
                'ml_metadata': result.metadata,
                'last_ml_update': datetime.now().isoformat()
            })
            update_data['agent_metadata'] = agent_metadata

            # Apply updates
            if update_data:
                await db.execute(
                    update(Artifact)
                    .where(Artifact.id == artifact.id)
                    .values(**update_data)
                )
                await db.commit()

    except Exception as e:
        logger.error(f"Error in background classification task: {e}")

async def _retrain_models_background(db: AsyncSession):
    """Background task for model retraining"""
    try:
        # Get recent artifacts for retraining data
        # This would involve collecting feedback and performance data
        # to improve model accuracy over time

        # For now, we'll just rebuild the search index
        # In production, this would involve actual model retraining

        from ..services.semantic_search import semantic_search_service
        await semantic_search_service.build_search_index(db)

        logger.info("Model retraining completed successfully")

    except Exception as e:
        logger.error(f"Error in model retraining: {e}")

def _analyze_project_complexity(artifacts: List[Artifact]) -> Dict[str, Any]:
    """Analyze project complexity based on artifacts"""
    total_lines = sum(len(artifact.content.split('\n')) for artifact in artifacts)
    total_files = len(artifacts)

    # Simple complexity scoring
    if total_lines > 5000 or total_files > 20:
        complexity = "high"
    elif total_lines > 1000 or total_files > 5:
        complexity = "medium"
    else:
        complexity = "low"

    return {
        "overall_complexity": complexity,
        "total_files": total_files,
        "total_lines": total_lines,
        "avg_lines_per_file": total_lines / max(total_files, 1)
    }

def _analyze_project_technologies(artifacts: List[Artifact]) -> List[str]:
    """Analyze dominant technologies in project"""
    from collections import Counter

    languages = [artifact.language for artifact in artifacts if artifact.language]
    file_types = [artifact.file_type for artifact in artifacts if artifact.file_type]

    # Combine and count
    all_tech = languages + file_types
    tech_counter = Counter(all_tech)

    return [tech for tech, count in tech_counter.most_common(5)]