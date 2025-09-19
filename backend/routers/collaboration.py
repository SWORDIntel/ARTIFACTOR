"""
Collaboration API router for ARTIFACTOR v3.0
Handles WebSocket connections, comments, activities, and notifications
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, desc
from pydantic import BaseModel

from ..database import AsyncSessionLocal
from ..models.collaboration import (
    CollaborationComment, CollaborationActivity, UserPresence,
    CollaborationNotification, ArtifactCollaboration
)
from ..services.websocket_manager import websocket_manager, MessageType
from ..services.presence_tracker import PresenceTracker
from ..services.notification_service import NotificationService, NotificationType, NotificationPriority
from ..auth import get_current_user
from ..models import User

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

# Service instances
presence_tracker = PresenceTracker()
notification_service = NotificationService()


# Pydantic models for API
class CommentCreate(BaseModel):
    content: str
    content_type: str = "text"
    parent_id: Optional[str] = None
    position_data: Optional[Dict[str, Any]] = None
    mentions: Optional[List[str]] = None


class CommentUpdate(BaseModel):
    content: str
    content_type: str = "text"


class NotificationMarkRead(BaseModel):
    notification_ids: List[str]


# WebSocket endpoint for real-time collaboration
@router.websocket("/ws/{artifact_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    artifact_id: str,
    token: str = Query(...),
):
    """WebSocket endpoint for real-time collaboration on artifacts"""
    try:
        # Authenticate user from token
        # Note: In production, implement proper JWT token validation
        user_id = token  # Simplified for this implementation

        # Get user data
        async with AsyncSessionLocal() as session:
            user = await session.get(User, user_id)
            if not user:
                await websocket.close(code=4001, reason="Invalid user")
                return

            user_data = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "display_name": getattr(user, 'display_name', user.username)
            }

        # Connect user to collaboration room
        await websocket_manager.connect_user(websocket, user_id, artifact_id, user_data)

        try:
            while True:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle the message
                await websocket_manager.handle_message(user_id, artifact_id, message)

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for user {user_id} on artifact {artifact_id}")

    except Exception as e:
        logger.error(f"WebSocket error for artifact {artifact_id}: {e}")
        await websocket.close(code=4000, reason="Internal error")

    finally:
        # Clean up user connection
        await websocket_manager.disconnect_user(user_id, artifact_id)


# Comment endpoints
@router.post("/artifacts/{artifact_id}/comments")
async def create_comment(
    artifact_id: str,
    comment: CommentCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(AsyncSessionLocal)
):
    """Create a new comment on an artifact"""
    try:
        # Create comment
        new_comment = CollaborationComment(
            id=str(uuid4()),
            artifact_id=artifact_id,
            user_id=current_user.id,
            parent_id=comment.parent_id,
            content=comment.content,
            content_type=comment.content_type,
            position_data=comment.position_data,
            mentions=comment.mentions or []
        )

        session.add(new_comment)
        await session.commit()
        await session.refresh(new_comment)

        # Log activity
        activity = CollaborationActivity(
            id=str(uuid4()),
            artifact_id=artifact_id,
            user_id=current_user.id,
            activity_type="comment_add",
            activity_category="comment",
            description=f"Added a comment",
            data={
                "comment_id": new_comment.id,
                "content_preview": comment.content[:100],
                "parent_id": comment.parent_id
            },
            related_comment_id=new_comment.id
        )
        session.add(activity)
        await session.commit()

        # Handle mentions
        if comment.mentions:
            for mentioned_username in comment.mentions:
                # Find mentioned user
                mentioned_user_result = await session.execute(
                    select(User).where(User.username == mentioned_username.replace("@", ""))
                )
                mentioned_user = mentioned_user_result.scalar_one_or_none()

                if mentioned_user:
                    await notification_service.create_mention_notification(
                        mentioned_user_id=mentioned_user.id,
                        mentioning_user_id=current_user.id,
                        artifact_id=artifact_id,
                        comment_id=new_comment.id,
                        mention_context=comment.content
                    )

        # Handle reply notifications
        if comment.parent_id:
            parent_comment = await session.get(CollaborationComment, comment.parent_id)
            if parent_comment and parent_comment.user_id != current_user.id:
                await notification_service.create_comment_reply_notification(
                    parent_comment_author_id=parent_comment.user_id,
                    replying_user_id=current_user.id,
                    artifact_id=artifact_id,
                    comment_id=new_comment.id,
                    reply_content=comment.content
                )

        # Broadcast to WebSocket connections
        if artifact_id in websocket_manager.rooms:
            room = websocket_manager.rooms[artifact_id]
            await room.broadcast_to_all({
                "type": MessageType.COMMENT_ADD.value,
                "user_id": current_user.id,
                "data": {
                    "comment_id": new_comment.id,
                    "content": comment.content,
                    "parent_id": comment.parent_id,
                    "position_data": comment.position_data,
                    "mentions": comment.mentions,
                    "user": {
                        "id": current_user.id,
                        "username": current_user.username
                    }
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

        return {
            "id": new_comment.id,
            "artifact_id": artifact_id,
            "content": comment.content,
            "content_type": comment.content_type,
            "parent_id": comment.parent_id,
            "position_data": comment.position_data,
            "mentions": comment.mentions,
            "created_at": new_comment.created_at.isoformat(),
            "user": {
                "id": current_user.id,
                "username": current_user.username
            }
        }

    except Exception as e:
        logger.error(f"Failed to create comment: {e}")
        raise HTTPException(status_code=500, detail="Failed to create comment")


@router.get("/artifacts/{artifact_id}/comments")
async def get_comments(
    artifact_id: str,
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    parent_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(AsyncSessionLocal)
):
    """Get comments for an artifact"""
    try:
        query = select(CollaborationComment).where(
            CollaborationComment.artifact_id == artifact_id
        )

        if parent_id is not None:
            query = query.where(CollaborationComment.parent_id == parent_id)
        else:
            query = query.where(CollaborationComment.parent_id.is_(None))

        query = query.order_by(desc(CollaborationComment.created_at)).offset(offset).limit(limit)

        result = await session.execute(query)
        comments = result.scalars().all()

        # Get user information for comments
        comment_data = []
        for comment in comments:
            user = await session.get(User, comment.user_id)

            comment_data.append({
                "id": comment.id,
                "content": comment.content,
                "content_type": comment.content_type,
                "parent_id": comment.parent_id,
                "position_data": comment.position_data,
                "mentions": comment.mentions,
                "reactions": comment.reactions,
                "created_at": comment.created_at.isoformat(),
                "updated_at": comment.updated_at.isoformat(),
                "edited": comment.edited,
                "resolved": comment.resolved,
                "resolved_at": comment.resolved_at.isoformat() if comment.resolved_at else None,
                "user": {
                    "id": user.id,
                    "username": user.username
                } if user else None
            })

        return {
            "comments": comment_data,
            "total": len(comments),
            "offset": offset,
            "limit": limit
        }

    except Exception as e:
        logger.error(f"Failed to get comments: {e}")
        raise HTTPException(status_code=500, detail="Failed to get comments")


@router.put("/artifacts/{artifact_id}/comments/{comment_id}")
async def update_comment(
    artifact_id: str,
    comment_id: str,
    comment_update: CommentUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(AsyncSessionLocal)
):
    """Update a comment"""
    try:
        # Get existing comment
        comment = await session.get(CollaborationComment, comment_id)
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")

        if comment.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to edit this comment")

        # Update comment
        comment.content = comment_update.content
        comment.content_type = comment_update.content_type
        comment.edited = True
        comment.updated_at = datetime.now(timezone.utc)

        await session.commit()

        # Log activity
        activity = CollaborationActivity(
            id=str(uuid4()),
            artifact_id=artifact_id,
            user_id=current_user.id,
            activity_type="comment_update",
            activity_category="comment",
            description=f"Updated a comment",
            data={
                "comment_id": comment_id,
                "content_preview": comment_update.content[:100]
            },
            related_comment_id=comment_id
        )
        session.add(activity)
        await session.commit()

        # Broadcast update
        if artifact_id in websocket_manager.rooms:
            room = websocket_manager.rooms[artifact_id]
            await room.broadcast_to_all({
                "type": MessageType.COMMENT_UPDATE.value,
                "user_id": current_user.id,
                "data": {
                    "comment_id": comment_id,
                    "content": comment_update.content,
                    "content_type": comment_update.content_type,
                    "edited": True
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

        return {
            "id": comment_id,
            "content": comment_update.content,
            "content_type": comment_update.content_type,
            "edited": True,
            "updated_at": comment.updated_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update comment: {e}")
        raise HTTPException(status_code=500, detail="Failed to update comment")


@router.delete("/artifacts/{artifact_id}/comments/{comment_id}")
async def delete_comment(
    artifact_id: str,
    comment_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(AsyncSessionLocal)
):
    """Delete a comment"""
    try:
        comment = await session.get(CollaborationComment, comment_id)
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")

        if comment.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this comment")

        await session.delete(comment)
        await session.commit()

        # Log activity
        activity = CollaborationActivity(
            id=str(uuid4()),
            artifact_id=artifact_id,
            user_id=current_user.id,
            activity_type="comment_delete",
            activity_category="comment",
            description=f"Deleted a comment",
            data={"comment_id": comment_id}
        )
        session.add(activity)
        await session.commit()

        # Broadcast deletion
        if artifact_id in websocket_manager.rooms:
            room = websocket_manager.rooms[artifact_id]
            await room.broadcast_to_all({
                "type": MessageType.COMMENT_DELETE.value,
                "user_id": current_user.id,
                "data": {"comment_id": comment_id},
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

        return {"message": "Comment deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete comment: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete comment")


# Activity endpoints
@router.get("/artifacts/{artifact_id}/activity")
async def get_activity_feed(
    artifact_id: str,
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    activity_types: Optional[List[str]] = Query(None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(AsyncSessionLocal)
):
    """Get activity feed for an artifact"""
    try:
        query = select(CollaborationActivity).where(
            CollaborationActivity.artifact_id == artifact_id
        )

        if activity_types:
            query = query.where(CollaborationActivity.activity_type.in_(activity_types))

        query = query.order_by(desc(CollaborationActivity.timestamp)).offset(offset).limit(limit)

        result = await session.execute(query)
        activities = result.scalars().all()

        activity_data = []
        for activity in activities:
            user = await session.get(User, activity.user_id)

            activity_data.append({
                "id": activity.id,
                "activity_type": activity.activity_type,
                "activity_category": activity.activity_category,
                "description": activity.description,
                "data": activity.data,
                "timestamp": activity.timestamp.isoformat(),
                "visibility": activity.visibility,
                "tags": activity.tags,
                "user": {
                    "id": user.id,
                    "username": user.username
                } if user else None
            })

        return {
            "activities": activity_data,
            "total": len(activities),
            "offset": offset,
            "limit": limit
        }

    except Exception as e:
        logger.error(f"Failed to get activity feed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get activity feed")


# Presence endpoints
@router.get("/artifacts/{artifact_id}/presence")
async def get_artifact_presence(
    artifact_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get active users for an artifact"""
    try:
        active_users = await websocket_manager.get_active_users(artifact_id)
        return {
            "artifact_id": artifact_id,
            "active_users": active_users,
            "total_count": len(active_users)
        }

    except Exception as e:
        logger.error(f"Failed to get artifact presence: {e}")
        raise HTTPException(status_code=500, detail="Failed to get presence")


# Notification endpoints
@router.get("/notifications")
async def get_notifications(
    limit: int = Query(50, le=100),
    unread_only: bool = Query(False),
    artifact_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """Get notifications for the current user"""
    try:
        notifications = await notification_service.get_user_notifications(
            user_id=current_user.id,
            limit=limit,
            unread_only=unread_only,
            artifact_id=artifact_id
        )

        return {
            "notifications": notifications,
            "total": len(notifications)
        }

    except Exception as e:
        logger.error(f"Failed to get notifications: {e}")
        raise HTTPException(status_code=500, detail="Failed to get notifications")


@router.post("/notifications/mark-read")
async def mark_notifications_read(
    mark_read: NotificationMarkRead,
    current_user: User = Depends(get_current_user)
):
    """Mark notifications as read"""
    try:
        success_count = 0
        for notification_id in mark_read.notification_ids:
            if await notification_service.mark_notification_read(notification_id, current_user.id):
                success_count += 1

        return {
            "marked_read": success_count,
            "total_requested": len(mark_read.notification_ids)
        }

    except Exception as e:
        logger.error(f"Failed to mark notifications as read: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark notifications as read")


@router.post("/notifications/mark-all-read")
async def mark_all_notifications_read(
    artifact_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """Mark all notifications as read"""
    try:
        marked_count = await notification_service.mark_all_read(
            user_id=current_user.id,
            artifact_id=artifact_id
        )

        return {"marked_read": marked_count}

    except Exception as e:
        logger.error(f"Failed to mark all notifications as read: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark all notifications as read")


@router.get("/notifications/counts")
async def get_notification_counts(current_user: User = Depends(get_current_user)):
    """Get notification counts for the current user"""
    try:
        counts = await notification_service.get_notification_counts(current_user.id)
        return counts

    except Exception as e:
        logger.error(f"Failed to get notification counts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get notification counts")