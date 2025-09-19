"""
Semantic Search Router for ARTIFACTOR v3.0
Advanced semantic search with natural language queries and ML-powered recommendations
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

# Database and models
from ..database import get_database
from ..models import Artifact, User
from ..routers.auth import get_current_user

# ML services
from ..services.semantic_search import semantic_search_service

# Pydantic schemas
from pydantic import BaseModel, Field

router = APIRouter()

# Request/Response models
class SemanticSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    search_type: str = Field("hybrid", regex="^(semantic|keyword|hybrid)$", description="Search method")
    limit: int = Field(20, ge=1, le=100, description="Maximum results")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters")

class SearchFilters(BaseModel):
    file_type: Optional[str] = None
    language: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    min_size: Optional[int] = None
    max_size: Optional[int] = None
    owner: Optional[str] = None
    has_tags: Optional[List[str]] = None

class SearchResult(BaseModel):
    id: str
    title: str
    description: Optional[str]
    file_type: str
    language: Optional[str]
    owner: Optional[str]
    created_at: datetime
    tags: List[str]
    relevance_score: float
    view_count: int
    download_count: int
    snippet: Optional[str] = None

class SemanticSearchResponse(BaseModel):
    query: str
    processed_query: Dict[str, Any]
    search_type: str
    results: List[SearchResult]
    total_results: int
    response_time_ms: float
    suggestions: Optional[List[str]] = None
    filters_applied: Optional[Dict[str, Any]] = None

class RelatedArtifactsRequest(BaseModel):
    artifact_id: uuid.UUID
    limit: int = Field(5, ge=1, le=20)

class RelatedArtifactsResponse(BaseModel):
    artifact_id: str
    related_artifacts: List[SearchResult]
    total_found: int

class SearchSuggestionsRequest(BaseModel):
    partial_query: str = Field(..., min_length=1, max_length=100)
    limit: int = Field(10, ge=1, le=20)

class SearchSuggestionsResponse(BaseModel):
    suggestions: List[str]
    categories: List[str]
    popular_queries: List[str]

class SearchAnalyticsResponse(BaseModel):
    total_searches: int
    search_types: Dict[str, int]
    popular_queries: List[str]
    avg_response_time: float
    cache_performance: Dict[str, Any]

@router.post("/search", response_model=SemanticSearchResponse)
async def semantic_search(
    request: SemanticSearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
):
    """
    Perform semantic search on artifacts
    Supports natural language queries with intelligent content matching
    """
    try:
        # Perform search
        search_result = await semantic_search_service.search(
            query=request.query,
            db=db,
            user_id=str(current_user.id),
            search_type=request.search_type,
            limit=request.limit,
            filters=request.filters
        )

        # Convert results to response format
        search_results = []
        for result in search_result.get('results', []):
            search_results.append(SearchResult(
                id=result['id'],
                title=result['title'],
                description=result.get('description'),
                file_type=result['file_type'],
                language=result.get('language'),
                owner=result.get('owner'),
                created_at=result['created_at'],
                tags=result.get('tags', []),
                relevance_score=result['relevance_score'],
                view_count=result.get('view_count', 0),
                download_count=result.get('download_count', 0),
                snippet=_generate_snippet(result.get('content', ''), request.query)
            ))

        # Generate search suggestions
        suggestions = await _generate_search_suggestions(request.query, current_user.id, db)

        return SemanticSearchResponse(
            query=search_result['query'],
            processed_query=search_result['processed_query'],
            search_type=search_result['search_type'],
            results=search_results,
            total_results=search_result['total_results'],
            response_time_ms=search_result['response_time_ms'],
            suggestions=suggestions,
            filters_applied=request.filters
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search error: {str(e)}"
        )

@router.get("/search", response_model=SemanticSearchResponse)
async def search_artifacts_get(
    q: str = Query(..., description="Search query"),
    search_type: str = Query("hybrid", regex="^(semantic|keyword|hybrid)$"),
    limit: int = Query(20, ge=1, le=100),
    file_type: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
):
    """
    Search artifacts using GET method (for simple queries)
    Convenient endpoint for basic search functionality
    """
    # Build filters
    filters = {}
    if file_type:
        filters['file_type'] = file_type
    if language:
        filters['language'] = language

    # Create request object
    request = SemanticSearchRequest(
        query=q,
        search_type=search_type,
        limit=limit,
        filters=filters if filters else None
    )

    return await semantic_search(request, current_user, db)

@router.post("/related", response_model=RelatedArtifactsResponse)
async def find_related_artifacts(
    request: RelatedArtifactsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
):
    """
    Find artifacts related to a specific artifact using content similarity
    """
    try:
        # Verify user has access to the artifact
        query = select(Artifact).where(
            Artifact.id == request.artifact_id,
            (Artifact.owner_id == current_user.id) | (Artifact.is_public == True)
        )
        result = await db.execute(query)
        artifact = result.scalar_one_or_none()

        if not artifact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Artifact not found or access denied"
            )

        # Find related artifacts
        related_results = await semantic_search_service.suggest_related_artifacts(
            artifact_id=str(request.artifact_id),
            db=db,
            limit=request.limit
        )

        # Convert to response format
        related_artifacts = []
        for result in related_results:
            related_artifacts.append(SearchResult(
                id=result['id'],
                title=result['title'],
                description=result.get('description'),
                file_type=result['file_type'],
                language=result.get('language'),
                owner=result.get('owner'),
                created_at=result['created_at'],
                tags=result.get('tags', []),
                relevance_score=result['relevance_score'],
                view_count=result.get('view_count', 0),
                download_count=result.get('download_count', 0)
            ))

        return RelatedArtifactsResponse(
            artifact_id=str(request.artifact_id),
            related_artifacts=related_artifacts,
            total_found=len(related_artifacts)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error finding related artifacts: {str(e)}"
        )

@router.post("/suggestions", response_model=SearchSuggestionsResponse)
async def get_search_suggestions(
    request: SearchSuggestionsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
):
    """
    Get search suggestions and autocomplete for partial queries
    """
    try:
        # Generate suggestions based on partial query
        suggestions = await _generate_autocomplete_suggestions(
            request.partial_query,
            current_user.id,
            db,
            request.limit
        )

        # Get popular categories
        categories = await _get_popular_categories(current_user.id, db)

        # Get popular search queries
        popular_queries = await _get_popular_queries(current_user.id, db)

        return SearchSuggestionsResponse(
            suggestions=suggestions,
            categories=categories,
            popular_queries=popular_queries
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating suggestions: {str(e)}"
        )

@router.post("/index/rebuild")
async def rebuild_search_index(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
):
    """
    Rebuild the search index for improved search performance
    Admin-only endpoint for index maintenance
    """
    try:
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )

        # Add index rebuild task to background
        background_tasks.add_task(_rebuild_search_index_background, db)

        return {
            "message": "Search index rebuild started",
            "status": "processing",
            "estimated_time_minutes": 10
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting index rebuild: {str(e)}"
        )

@router.get("/analytics", response_model=SearchAnalyticsResponse)
async def get_search_analytics(
    current_user: User = Depends(get_current_user)
):
    """
    Get search analytics and performance metrics
    """
    try:
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )

        # Get search analytics
        analytics = await semantic_search_service.get_search_analytics()

        return SearchAnalyticsResponse(
            total_searches=analytics['metrics']['total_searches'],
            search_types={
                'semantic': analytics['metrics']['semantic_searches'],
                'keyword': analytics['metrics']['keyword_searches'],
                'hybrid': analytics['metrics']['hybrid_searches']
            },
            popular_queries=[],  # Would be populated from search logs
            avg_response_time=analytics['metrics']['avg_response_time'],
            cache_performance=analytics['cache_stats']
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving analytics: {str(e)}"
        )

@router.get("/status")
async def get_search_status(
    current_user: User = Depends(get_current_user)
):
    """
    Get search service status and health information
    """
    try:
        analytics = await semantic_search_service.get_search_analytics()

        return {
            "status": "healthy",
            "search_service": {
                "embeddings_available": analytics['index_status'].get('embeddings_count', 0) > 0,
                "last_index_update": analytics['index_status'].get('last_updated'),
                "total_artifacts_indexed": analytics['index_status'].get('total_artifacts', 0),
                "index_size_mb": analytics['index_status'].get('index_size_mb', 0)
            },
            "performance": {
                "avg_response_time": analytics['metrics']['avg_response_time'],
                "cache_hit_rate": analytics['cache_stats'].get('cache_size', 0) / max(analytics['metrics']['total_searches'], 1)
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving status: {str(e)}"
        )

# Helper functions
def _generate_snippet(content: str, query: str, max_length: int = 200) -> str:
    """Generate a content snippet highlighting query relevance"""
    if not content or not query:
        return content[:max_length] + "..." if len(content) > max_length else content

    # Simple snippet generation - find query terms in content
    query_terms = query.lower().split()
    content_lower = content.lower()

    # Find best position to show snippet
    best_pos = 0
    max_matches = 0

    for i in range(0, len(content) - max_length, 50):
        snippet = content[i:i + max_length].lower()
        matches = sum(1 for term in query_terms if term in snippet)
        if matches > max_matches:
            max_matches = matches
            best_pos = i

    snippet = content[best_pos:best_pos + max_length]
    if best_pos > 0:
        snippet = "..." + snippet
    if best_pos + max_length < len(content):
        snippet = snippet + "..."

    return snippet

async def _generate_search_suggestions(query: str, user_id: str, db: AsyncSession) -> List[str]:
    """Generate search suggestions based on query"""
    # Simple suggestion generation
    suggestions = []

    # Add common search refinements
    if "python" in query.lower():
        suggestions.extend(["python flask", "python django", "python machine learning"])
    elif "javascript" in query.lower():
        suggestions.extend(["javascript react", "javascript node", "javascript vue"])
    elif "api" in query.lower():
        suggestions.extend(["rest api", "graphql api", "api documentation"])

    return suggestions[:5]

async def _generate_autocomplete_suggestions(
    partial_query: str, user_id: str, db: AsyncSession, limit: int
) -> List[str]:
    """Generate autocomplete suggestions"""
    # Simple autocomplete based on common terms
    common_terms = [
        "python flask", "javascript react", "vue.js", "django", "api documentation",
        "machine learning", "data analysis", "authentication", "database design",
        "testing framework", "deployment script", "configuration file"
    ]

    # Filter based on partial query
    suggestions = [
        term for term in common_terms
        if partial_query.lower() in term.lower()
    ]

    return suggestions[:limit]

async def _get_popular_categories(user_id: str, db: AsyncSession) -> List[str]:
    """Get popular categories for user's artifacts"""
    try:
        # Query for most common categories
        # This would involve aggregating category data from artifacts
        return ["web-development", "data-science", "api-development", "testing", "documentation"]
    except Exception:
        return []

async def _get_popular_queries(user_id: str, db: AsyncSession) -> List[str]:
    """Get popular search queries"""
    # In a real implementation, this would query search logs
    return ["authentication", "api", "python", "javascript", "database"]

async def _rebuild_search_index_background(db: AsyncSession):
    """Background task for rebuilding search index"""
    try:
        await semantic_search_service.build_search_index(db)
        logger.info("Search index rebuilt successfully")
    except Exception as e:
        logger.error(f"Error rebuilding search index: {e}")