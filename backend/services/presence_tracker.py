"""
Real-time presence tracking service for ARTIFACTOR v3.0
Tracks user presence, activity, and location within artifacts
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
from uuid import uuid4

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from ..config import settings
from ..database import AsyncSessionLocal
from ..models.collaboration import UserPresence

logger = logging.getLogger(__name__)


class PresenceTracker:
    """Tracks user presence across artifacts in real-time"""

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.presence_cache: Dict[str, Dict[str, Any]] = {}  # user_id:artifact_id -> presence data
        self.cleanup_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Initialize the presence tracker with Redis connection"""
        try:
            if settings.REDIS_URL:
                self.redis_client = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    health_check_interval=30
                )
                await self.redis_client.ping()
                logger.info("Presence tracker initialized with Redis")

                # Start cleanup task
                self.cleanup_task = asyncio.create_task(self._cleanup_expired_presence())
            else:
                logger.warning("Redis not configured, using in-memory presence tracking")

        except Exception as e:
            logger.error(f"Failed to initialize Redis for presence tracker: {e}")
            self.redis_client = None

    async def cleanup(self):
        """Cleanup presence tracker resources"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass

        if self.redis_client:
            await self.redis_client.close()

    async def update_presence(
        self,
        user_id: str,
        artifact_id: str,
        status: str,
        activity: Optional[str] = None,
        cursor_position: Optional[Dict[str, Any]] = None,
        viewport: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        connection_info: Optional[Dict[str, Any]] = None
    ):
        """Update user presence information"""
        presence_key = f"{user_id}:{artifact_id}"
        now = datetime.now(timezone.utc)

        presence_data = {
            "user_id": user_id,
            "artifact_id": artifact_id,
            "status": status,
            "activity": activity,
            "cursor_position": cursor_position,
            "viewport": viewport,
            "last_seen": now.isoformat(),
            "session_id": session_id,
            "connection_info": connection_info or {}
        }

        # Update in-memory cache
        self.presence_cache[presence_key] = presence_data

        # Update in Redis if available
        if self.redis_client:
            try:
                redis_key = f"presence:{presence_key}"
                await self.redis_client.hset(redis_key, mapping={
                    k: str(v) if v is not None else ""
                    for k, v in presence_data.items()
                })
                # Set TTL for automatic cleanup
                await self.redis_client.expire(redis_key, 300)  # 5 minutes
            except Exception as e:
                logger.error(f"Failed to update presence in Redis: {e}")

        # Update database
        try:
            await self._update_presence_in_db(presence_data)
        except Exception as e:
            logger.error(f"Failed to update presence in database: {e}")

    async def remove_presence(self, user_id: str, artifact_id: str):
        """Remove user presence information"""
        presence_key = f"{user_id}:{artifact_id}"

        # Remove from cache
        self.presence_cache.pop(presence_key, None)

        # Remove from Redis
        if self.redis_client:
            try:
                redis_key = f"presence:{presence_key}"
                await self.redis_client.delete(redis_key)
            except Exception as e:
                logger.error(f"Failed to remove presence from Redis: {e}")

        # Update database to offline status
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(
                    update(UserPresence)
                    .where(UserPresence.user_id == user_id)
                    .where(UserPresence.artifact_id == artifact_id)
                    .values(
                        status="offline",
                        last_seen=datetime.now(timezone.utc)
                    )
                )
                await session.commit()
        except Exception as e:
            logger.error(f"Failed to update presence to offline in database: {e}")

    async def get_artifact_presence(self, artifact_id: str) -> List[Dict[str, Any]]:
        """Get all active users for an artifact"""
        active_users = []

        # First check cache
        for presence_key, presence_data in self.presence_cache.items():
            if (presence_data.get("artifact_id") == artifact_id and
                presence_data.get("status") in ["active", "away"]):
                active_users.append(presence_data)

        # If Redis is available, also check there
        if self.redis_client:
            try:
                pattern = f"presence:*:{artifact_id}"
                async for key in self.redis_client.scan_iter(match=pattern):
                    presence_data = await self.redis_client.hgetall(key)
                    if presence_data and presence_data.get("status") in ["active", "away"]:
                        # Convert Redis data back to proper format
                        parsed_data = self._parse_redis_presence_data(presence_data)
                        active_users.append(parsed_data)
            except Exception as e:
                logger.error(f"Failed to get artifact presence from Redis: {e}")

        # Deduplicate based on user_id
        seen_users = set()
        unique_users = []
        for user_data in active_users:
            user_id = user_data.get("user_id")
            if user_id and user_id not in seen_users:
                seen_users.add(user_id)
                unique_users.append(user_data)

        return unique_users

    async def get_user_presence(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all presence information for a user across artifacts"""
        user_presence = []

        # Check cache
        for presence_key, presence_data in self.presence_cache.items():
            if (presence_data.get("user_id") == user_id and
                presence_data.get("status") in ["active", "away"]):
                user_presence.append(presence_data)

        # Check Redis if available
        if self.redis_client:
            try:
                pattern = f"presence:{user_id}:*"
                async for key in self.redis_client.scan_iter(match=pattern):
                    presence_data = await self.redis_client.hgetall(key)
                    if presence_data and presence_data.get("status") in ["active", "away"]:
                        parsed_data = self._parse_redis_presence_data(presence_data)
                        user_presence.append(parsed_data)
            except Exception as e:
                logger.error(f"Failed to get user presence from Redis: {e}")

        return user_presence

    async def get_presence_summary(self, artifact_id: str) -> Dict[str, Any]:
        """Get presence summary for an artifact"""
        active_users = await self.get_artifact_presence(artifact_id)

        summary = {
            "artifact_id": artifact_id,
            "total_users": len(active_users),
            "active_count": len([u for u in active_users if u.get("status") == "active"]),
            "away_count": len([u for u in active_users if u.get("status") == "away"]),
            "activities": {},
            "users": active_users,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Count activities
        for user in active_users:
            activity = user.get("activity")
            if activity:
                summary["activities"][activity] = summary["activities"].get(activity, 0) + 1

        return summary

    async def update_cursor_position(self, user_id: str, artifact_id: str, cursor_position: Dict[str, Any]):
        """Update just the cursor position for a user"""
        presence_key = f"{user_id}:{artifact_id}"

        if presence_key in self.presence_cache:
            self.presence_cache[presence_key]["cursor_position"] = cursor_position
            self.presence_cache[presence_key]["last_seen"] = datetime.now(timezone.utc).isoformat()

        # Update in Redis
        if self.redis_client:
            try:
                redis_key = f"presence:{presence_key}"
                await self.redis_client.hset(redis_key, "cursor_position", str(cursor_position))
                await self.redis_client.hset(redis_key, "last_seen", datetime.now(timezone.utc).isoformat())
            except Exception as e:
                logger.error(f"Failed to update cursor position in Redis: {e}")

    async def update_activity(self, user_id: str, artifact_id: str, activity: str):
        """Update just the activity for a user"""
        presence_key = f"{user_id}:{artifact_id}"

        if presence_key in self.presence_cache:
            self.presence_cache[presence_key]["activity"] = activity
            self.presence_cache[presence_key]["last_seen"] = datetime.now(timezone.utc).isoformat()

        # Update in Redis
        if self.redis_client:
            try:
                redis_key = f"presence:{presence_key}"
                await self.redis_client.hset(redis_key, "activity", activity)
                await self.redis_client.hset(redis_key, "last_seen", datetime.now(timezone.utc).isoformat())
            except Exception as e:
                logger.error(f"Failed to update activity in Redis: {e}")

    async def _update_presence_in_db(self, presence_data: Dict[str, Any]):
        """Update presence information in the database"""
        async with AsyncSessionLocal() as session:
            # Check if presence record exists
            result = await session.execute(
                select(UserPresence)
                .where(UserPresence.user_id == presence_data["user_id"])
                .where(UserPresence.artifact_id == presence_data["artifact_id"])
            )
            existing_presence = result.scalar_one_or_none()

            if existing_presence:
                # Update existing record
                await session.execute(
                    update(UserPresence)
                    .where(UserPresence.id == existing_presence.id)
                    .values(
                        status=presence_data["status"],
                        activity=presence_data["activity"],
                        cursor_position=presence_data["cursor_position"],
                        viewport=presence_data["viewport"],
                        last_seen=datetime.fromisoformat(presence_data["last_seen"]),
                        session_id=presence_data["session_id"],
                        connection_info=presence_data["connection_info"]
                    )
                )
            else:
                # Create new record
                new_presence = UserPresence(
                    user_id=presence_data["user_id"],
                    artifact_id=presence_data["artifact_id"],
                    status=presence_data["status"],
                    activity=presence_data["activity"],
                    cursor_position=presence_data["cursor_position"],
                    viewport=presence_data["viewport"],
                    last_seen=datetime.fromisoformat(presence_data["last_seen"]),
                    session_id=presence_data["session_id"],
                    connection_info=presence_data["connection_info"]
                )
                session.add(new_presence)

            await session.commit()

    def _parse_redis_presence_data(self, redis_data: Dict[str, str]) -> Dict[str, Any]:
        """Parse presence data from Redis string format"""
        import json

        parsed = {}
        for key, value in redis_data.items():
            if not value:
                parsed[key] = None
            elif key in ["cursor_position", "viewport", "connection_info"]:
                try:
                    parsed[key] = json.loads(value) if value else {}
                except (json.JSONDecodeError, TypeError):
                    parsed[key] = {}
            else:
                parsed[key] = value

        return parsed

    async def _cleanup_expired_presence(self):
        """Background task to cleanup expired presence records"""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute

                # Clean up in-memory cache
                expired_keys = []
                cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=5)

                for presence_key, presence_data in self.presence_cache.items():
                    last_seen_str = presence_data.get("last_seen")
                    if last_seen_str:
                        try:
                            last_seen = datetime.fromisoformat(last_seen_str)
                            if last_seen < cutoff_time:
                                expired_keys.append(presence_key)
                        except ValueError:
                            expired_keys.append(presence_key)

                for key in expired_keys:
                    self.presence_cache.pop(key, None)

                # Clean up database records
                try:
                    async with AsyncSessionLocal() as session:
                        # Mark old presence as offline
                        await session.execute(
                            update(UserPresence)
                            .where(UserPresence.last_seen < cutoff_time)
                            .where(UserPresence.status.in_(["active", "away"]))
                            .values(status="offline")
                        )
                        await session.commit()
                except Exception as e:
                    logger.error(f"Failed to cleanup expired presence in database: {e}")

                if expired_keys:
                    logger.info(f"Cleaned up {len(expired_keys)} expired presence records")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in presence cleanup task: {e}")

    async def get_presence_analytics(self, artifact_id: str, hours: int = 24) -> Dict[str, Any]:
        """Get presence analytics for an artifact"""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

            async with AsyncSessionLocal() as session:
                # Get presence data from the database
                result = await session.execute(
                    select(UserPresence)
                    .where(UserPresence.artifact_id == artifact_id)
                    .where(UserPresence.last_seen >= cutoff_time)
                )
                presence_records = result.scalars().all()

                # Calculate analytics
                unique_users = set()
                activity_counts = {}
                status_counts = {"active": 0, "away": 0, "offline": 0}

                for record in presence_records:
                    unique_users.add(record.user_id)
                    if record.activity:
                        activity_counts[record.activity] = activity_counts.get(record.activity, 0) + 1
                    status_counts[record.status] = status_counts.get(record.status, 0) + 1

                return {
                    "artifact_id": artifact_id,
                    "time_period_hours": hours,
                    "unique_users": len(unique_users),
                    "total_presence_events": len(presence_records),
                    "activity_breakdown": activity_counts,
                    "status_breakdown": status_counts,
                    "analyzed_at": datetime.now(timezone.utc).isoformat()
                }

        except Exception as e:
            logger.error(f"Failed to get presence analytics: {e}")
            return {
                "error": str(e),
                "artifact_id": artifact_id,
                "analyzed_at": datetime.now(timezone.utc).isoformat()
            }