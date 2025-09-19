"""
Notification service for ARTIFACTOR v3.0 collaboration features
Handles real-time notifications, mentions, and team communication
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timezone
from uuid import uuid4
from enum import Enum

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from ..config import settings
from ..database import AsyncSessionLocal
from ..models.collaboration import CollaborationNotification

logger = logging.getLogger(__name__)


class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationType(Enum):
    """Types of collaboration notifications"""
    MENTION = "mention"
    COMMENT_REPLY = "comment_reply"
    ARTIFACT_UPDATE = "artifact_update"
    USER_JOIN = "user_join"
    USER_LEAVE = "user_leave"
    WORKSPACE_INVITE = "workspace_invite"
    DEADLINE_REMINDER = "deadline_reminder"
    SYSTEM_ALERT = "system_alert"


class NotificationService:
    """Handles all collaboration notifications"""

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.notification_cache: Dict[str, List[Dict[str, Any]]] = {}  # user_id -> notifications
        self.subscribers: Dict[str, Set[callable]] = {}  # user_id -> callback functions
        self.delivery_queue: asyncio.Queue = asyncio.Queue()
        self.delivery_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Initialize the notification service"""
        try:
            if settings.REDIS_URL:
                self.redis_client = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    health_check_interval=30
                )
                await self.redis_client.ping()
                logger.info("Notification service initialized with Redis")

                # Start delivery task
                self.delivery_task = asyncio.create_task(self._process_delivery_queue())
            else:
                logger.warning("Redis not configured, using in-memory notifications")

        except Exception as e:
            logger.error(f"Failed to initialize Redis for notification service: {e}")
            self.redis_client = None

    async def cleanup(self):
        """Cleanup notification service resources"""
        if self.delivery_task:
            self.delivery_task.cancel()
            try:
                await self.delivery_task
            except asyncio.CancelledError:
                pass

        if self.redis_client:
            await self.redis_client.close()

    async def create_notification(
        self,
        user_id: str,
        type: NotificationType,
        title: str,
        message: str,
        artifact_id: Optional[str] = None,
        related_user_id: Optional[str] = None,
        related_comment_id: Optional[str] = None,
        related_activity_id: Optional[str] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        delivery_channels: Optional[List[str]] = None,
        data: Optional[Dict[str, Any]] = None,
        scheduled_for: Optional[datetime] = None
    ) -> str:
        """Create a new notification"""
        notification_id = str(uuid4())
        now = datetime.now(timezone.utc)

        notification_data = {
            "id": notification_id,
            "user_id": user_id,
            "artifact_id": artifact_id,
            "type": type.value,
            "title": title,
            "message": message,
            "related_user_id": related_user_id,
            "related_comment_id": related_comment_id,
            "related_activity_id": related_activity_id,
            "priority": priority.value,
            "delivery_channels": delivery_channels or ["websocket"],
            "delivered_channels": [],
            "read": False,
            "read_at": None,
            "created_at": now,
            "scheduled_for": scheduled_for or now,
            "data": data or {}
        }

        # Save to database
        try:
            async with AsyncSessionLocal() as session:
                notification = CollaborationNotification(
                    id=notification_id,
                    user_id=user_id,
                    artifact_id=artifact_id,
                    type=type.value,
                    title=title,
                    message=message,
                    related_user_id=related_user_id,
                    related_comment_id=related_comment_id,
                    related_activity_id=related_activity_id,
                    priority=priority.value,
                    delivery_channels=delivery_channels or ["websocket"],
                    delivered_channels=[],
                    read=False,
                    created_at=now,
                    scheduled_for=scheduled_for or now,
                    data=data or {}
                )
                session.add(notification)
                await session.commit()

        except Exception as e:
            logger.error(f"Failed to save notification to database: {e}")
            return notification_id

        # Add to cache
        if user_id not in self.notification_cache:
            self.notification_cache[user_id] = []
        self.notification_cache[user_id].append(notification_data)

        # Cache in Redis
        if self.redis_client:
            try:
                redis_key = f"notifications:{user_id}"
                await self.redis_client.lpush(redis_key, str(notification_data))
                await self.redis_client.ltrim(redis_key, 0, 100)  # Keep only latest 100
                await self.redis_client.expire(redis_key, 86400)  # 24 hours TTL
            except Exception as e:
                logger.error(f"Failed to cache notification in Redis: {e}")

        # Queue for delivery
        await self.delivery_queue.put(notification_data)

        logger.info(f"Created notification {notification_id} for user {user_id}")
        return notification_id

    async def create_mention_notification(
        self,
        mentioned_user_id: str,
        mentioning_user_id: str,
        artifact_id: str,
        comment_id: str,
        mention_context: str
    ):
        """Create a notification for user mentions"""
        # Get mentioning user info for the message
        from ..models import User
        async with AsyncSessionLocal() as session:
            mentioning_user = await session.get(User, mentioning_user_id)
            mentioning_username = mentioning_user.username if mentioning_user else "Someone"

        title = f"You were mentioned by {mentioning_username}"
        message = f"{mentioning_username} mentioned you in a comment: {mention_context[:100]}..."

        return await self.create_notification(
            user_id=mentioned_user_id,
            type=NotificationType.MENTION,
            title=title,
            message=message,
            artifact_id=artifact_id,
            related_user_id=mentioning_user_id,
            related_comment_id=comment_id,
            priority=NotificationPriority.HIGH,
            delivery_channels=["websocket", "email"],
            data={
                "mention_context": mention_context,
                "comment_id": comment_id,
                "artifact_id": artifact_id
            }
        )

    async def create_comment_reply_notification(
        self,
        parent_comment_author_id: str,
        replying_user_id: str,
        artifact_id: str,
        comment_id: str,
        reply_content: str
    ):
        """Create a notification for comment replies"""
        if parent_comment_author_id == replying_user_id:
            return  # Don't notify users about their own replies

        # Get replying user info
        from ..models import User
        async with AsyncSessionLocal() as session:
            replying_user = await session.get(User, replying_user_id)
            replying_username = replying_user.username if replying_user else "Someone"

        title = f"{replying_username} replied to your comment"
        message = f"{replying_username}: {reply_content[:100]}..."

        return await self.create_notification(
            user_id=parent_comment_author_id,
            type=NotificationType.COMMENT_REPLY,
            title=title,
            message=message,
            artifact_id=artifact_id,
            related_user_id=replying_user_id,
            related_comment_id=comment_id,
            priority=NotificationPriority.NORMAL,
            delivery_channels=["websocket"],
            data={
                "reply_content": reply_content,
                "comment_id": comment_id,
                "artifact_id": artifact_id
            }
        )

    async def create_artifact_update_notification(
        self,
        user_ids: List[str],
        updating_user_id: str,
        artifact_id: str,
        update_summary: str
    ):
        """Create notifications for artifact updates"""
        # Get updating user info
        from ..models import User
        async with AsyncSessionLocal() as session:
            updating_user = await session.get(User, updating_user_id)
            updating_username = updating_user.username if updating_user else "Someone"

        title = f"Artifact updated by {updating_username}"
        message = f"{updating_username} made changes: {update_summary[:100]}..."

        notifications = []
        for user_id in user_ids:
            if user_id != updating_user_id:  # Don't notify the user making the update
                notification_id = await self.create_notification(
                    user_id=user_id,
                    type=NotificationType.ARTIFACT_UPDATE,
                    title=title,
                    message=message,
                    artifact_id=artifact_id,
                    related_user_id=updating_user_id,
                    priority=NotificationPriority.NORMAL,
                    delivery_channels=["websocket"],
                    data={
                        "update_summary": update_summary,
                        "artifact_id": artifact_id
                    }
                )
                notifications.append(notification_id)

        return notifications

    async def mark_notification_read(self, notification_id: str, user_id: str) -> bool:
        """Mark a notification as read"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    update(CollaborationNotification)
                    .where(CollaborationNotification.id == notification_id)
                    .where(CollaborationNotification.user_id == user_id)
                    .values(
                        read=True,
                        read_at=datetime.now(timezone.utc)
                    )
                )
                await session.commit()

                if result.rowcount > 0:
                    # Update cache
                    if user_id in self.notification_cache:
                        for notification in self.notification_cache[user_id]:
                            if notification["id"] == notification_id:
                                notification["read"] = True
                                notification["read_at"] = datetime.now(timezone.utc)
                                break

                    logger.info(f"Marked notification {notification_id} as read for user {user_id}")
                    return True

                return False

        except Exception as e:
            logger.error(f"Failed to mark notification as read: {e}")
            return False

    async def mark_all_read(self, user_id: str, artifact_id: Optional[str] = None) -> int:
        """Mark all notifications as read for a user"""
        try:
            async with AsyncSessionLocal() as session:
                query = update(CollaborationNotification).where(
                    CollaborationNotification.user_id == user_id,
                    CollaborationNotification.read == False
                )

                if artifact_id:
                    query = query.where(CollaborationNotification.artifact_id == artifact_id)

                result = await session.execute(
                    query.values(
                        read=True,
                        read_at=datetime.now(timezone.utc)
                    )
                )
                await session.commit()

                # Update cache
                if user_id in self.notification_cache:
                    for notification in self.notification_cache[user_id]:
                        if not notification["read"] and (not artifact_id or notification["artifact_id"] == artifact_id):
                            notification["read"] = True
                            notification["read_at"] = datetime.now(timezone.utc)

                logger.info(f"Marked {result.rowcount} notifications as read for user {user_id}")
                return result.rowcount

        except Exception as e:
            logger.error(f"Failed to mark all notifications as read: {e}")
            return 0

    async def get_user_notifications(
        self,
        user_id: str,
        limit: int = 50,
        unread_only: bool = False,
        artifact_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get notifications for a user"""
        try:
            async with AsyncSessionLocal() as session:
                query = select(CollaborationNotification).where(
                    CollaborationNotification.user_id == user_id
                )

                if unread_only:
                    query = query.where(CollaborationNotification.read == False)

                if artifact_id:
                    query = query.where(CollaborationNotification.artifact_id == artifact_id)

                query = query.order_by(CollaborationNotification.created_at.desc()).limit(limit)

                result = await session.execute(query)
                notifications = result.scalars().all()

                return [
                    {
                        "id": notification.id,
                        "type": notification.type,
                        "title": notification.title,
                        "message": notification.message,
                        "artifact_id": notification.artifact_id,
                        "related_user_id": notification.related_user_id,
                        "related_comment_id": notification.related_comment_id,
                        "related_activity_id": notification.related_activity_id,
                        "priority": notification.priority,
                        "read": notification.read,
                        "read_at": notification.read_at.isoformat() if notification.read_at else None,
                        "created_at": notification.created_at.isoformat(),
                        "data": notification.data
                    }
                    for notification in notifications
                ]

        except Exception as e:
            logger.error(f"Failed to get user notifications: {e}")
            return []

    async def get_notification_counts(self, user_id: str) -> Dict[str, int]:
        """Get notification counts for a user"""
        try:
            async with AsyncSessionLocal() as session:
                # Total notifications
                total_result = await session.execute(
                    select(CollaborationNotification)
                    .where(CollaborationNotification.user_id == user_id)
                )
                total_count = len(total_result.scalars().all())

                # Unread notifications
                unread_result = await session.execute(
                    select(CollaborationNotification)
                    .where(CollaborationNotification.user_id == user_id)
                    .where(CollaborationNotification.read == False)
                )
                unread_count = len(unread_result.scalars().all())

                # High priority unread
                urgent_result = await session.execute(
                    select(CollaborationNotification)
                    .where(CollaborationNotification.user_id == user_id)
                    .where(CollaborationNotification.read == False)
                    .where(CollaborationNotification.priority.in_(["high", "urgent"]))
                )
                urgent_count = len(urgent_result.scalars().all())

                return {
                    "total": total_count,
                    "unread": unread_count,
                    "urgent": urgent_count
                }

        except Exception as e:
            logger.error(f"Failed to get notification counts: {e}")
            return {"total": 0, "unread": 0, "urgent": 0}

    async def subscribe_to_notifications(self, user_id: str, callback: callable):
        """Subscribe to real-time notifications for a user"""
        if user_id not in self.subscribers:
            self.subscribers[user_id] = set()
        self.subscribers[user_id].add(callback)

    async def unsubscribe_from_notifications(self, user_id: str, callback: callable):
        """Unsubscribe from real-time notifications"""
        if user_id in self.subscribers:
            self.subscribers[user_id].discard(callback)
            if not self.subscribers[user_id]:
                del self.subscribers[user_id]

    async def _process_delivery_queue(self):
        """Background task to process notification deliveries"""
        while True:
            try:
                notification = await self.delivery_queue.get()
                await self._deliver_notification(notification)
                self.delivery_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in notification delivery task: {e}")

    async def _deliver_notification(self, notification: Dict[str, Any]):
        """Deliver a notification through various channels"""
        user_id = notification["user_id"]
        delivery_channels = notification.get("delivery_channels", ["websocket"])
        delivered_channels = []

        # WebSocket delivery
        if "websocket" in delivery_channels and user_id in self.subscribers:
            try:
                for callback in self.subscribers[user_id]:
                    await callback(notification)
                delivered_channels.append("websocket")
            except Exception as e:
                logger.error(f"Failed to deliver WebSocket notification: {e}")

        # Update delivered channels in database
        if delivered_channels:
            try:
                async with AsyncSessionLocal() as session:
                    await session.execute(
                        update(CollaborationNotification)
                        .where(CollaborationNotification.id == notification["id"])
                        .values(delivered_channels=delivered_channels)
                    )
                    await session.commit()
            except Exception as e:
                logger.error(f"Failed to update delivered channels: {e}")

    async def delete_notification(self, notification_id: str, user_id: str) -> bool:
        """Delete a notification"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    delete(CollaborationNotification)
                    .where(CollaborationNotification.id == notification_id)
                    .where(CollaborationNotification.user_id == user_id)
                )
                await session.commit()

                if result.rowcount > 0:
                    # Remove from cache
                    if user_id in self.notification_cache:
                        self.notification_cache[user_id] = [
                            n for n in self.notification_cache[user_id]
                            if n["id"] != notification_id
                        ]

                    logger.info(f"Deleted notification {notification_id} for user {user_id}")
                    return True

                return False

        except Exception as e:
            logger.error(f"Failed to delete notification: {e}")
            return False