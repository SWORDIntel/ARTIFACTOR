"""
Real-time WebSocket manager for ARTIFACTOR v3.0 collaboration features
Supports multi-user collaboration, presence tracking, and real-time communication
"""

import json
import asyncio
import logging
from typing import Dict, List, Set, Optional, Any
from datetime import datetime, timezone
from uuid import uuid4
from enum import Enum

from fastapi import WebSocket, WebSocketDisconnect
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import AsyncSessionLocal
from .presence_tracker import PresenceTracker
from .notification_service import NotificationService

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """WebSocket message types for collaboration"""
    USER_JOIN = "user_join"
    USER_LEAVE = "user_leave"
    PRESENCE_UPDATE = "presence_update"
    ARTIFACT_EDIT = "artifact_edit"
    COMMENT_ADD = "comment_add"
    COMMENT_UPDATE = "comment_update"
    COMMENT_DELETE = "comment_delete"
    ACTIVITY_UPDATE = "activity_update"
    NOTIFICATION = "notification"
    TYPING_START = "typing_start"
    TYPING_STOP = "typing_stop"
    CURSOR_MOVE = "cursor_move"
    SELECTION_CHANGE = "selection_change"


class CollaborationRoom:
    """Represents a collaboration room for an artifact"""

    def __init__(self, artifact_id: str):
        self.artifact_id = artifact_id
        self.connections: Dict[str, WebSocket] = {}  # user_id -> websocket
        self.user_data: Dict[str, Dict[str, Any]] = {}  # user_id -> user data
        self.cursors: Dict[str, Dict[str, Any]] = {}  # user_id -> cursor position
        self.selections: Dict[str, Dict[str, Any]] = {}  # user_id -> selection data
        self.typing_users: Set[str] = set()
        self.created_at = datetime.now(timezone.utc)
        self.last_activity = datetime.now(timezone.utc)

    async def add_user(self, user_id: str, websocket: WebSocket, user_data: Dict[str, Any]):
        """Add a user to the collaboration room"""
        self.connections[user_id] = websocket
        self.user_data[user_id] = user_data
        self.last_activity = datetime.now(timezone.utc)

        # Notify other users about the new participant
        await self.broadcast_to_others(user_id, {
            "type": MessageType.USER_JOIN.value,
            "user_id": user_id,
            "user_data": user_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    async def remove_user(self, user_id: str):
        """Remove a user from the collaboration room"""
        if user_id in self.connections:
            del self.connections[user_id]
        if user_id in self.user_data:
            user_data = self.user_data.pop(user_id)
        if user_id in self.cursors:
            del self.cursors[user_id]
        if user_id in self.selections:
            del self.selections[user_id]
        if user_id in self.typing_users:
            self.typing_users.discard(user_id)

        self.last_activity = datetime.now(timezone.utc)

        # Notify other users about the departure
        await self.broadcast_to_others(user_id, {
            "type": MessageType.USER_LEAVE.value,
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Broadcast message to all users in the room"""
        if not self.connections:
            return

        message_str = json.dumps(message)
        disconnected_users = []

        for user_id, websocket in self.connections.items():
            try:
                await websocket.send_text(message_str)
            except WebSocketDisconnect:
                disconnected_users.append(user_id)
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
                disconnected_users.append(user_id)

        # Clean up disconnected users
        for user_id in disconnected_users:
            await self.remove_user(user_id)

    async def broadcast_to_others(self, sender_user_id: str, message: Dict[str, Any]):
        """Broadcast message to all users except the sender"""
        if not self.connections:
            return

        message_str = json.dumps(message)
        disconnected_users = []

        for user_id, websocket in self.connections.items():
            if user_id == sender_user_id:
                continue

            try:
                await websocket.send_text(message_str)
            except WebSocketDisconnect:
                disconnected_users.append(user_id)
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
                disconnected_users.append(user_id)

        # Clean up disconnected users
        for user_id in disconnected_users:
            await self.remove_user(user_id)

    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Send message to a specific user"""
        if user_id not in self.connections:
            return False

        try:
            message_str = json.dumps(message)
            await self.connections[user_id].send_text(message_str)
            return True
        except WebSocketDisconnect:
            await self.remove_user(user_id)
            return False
        except Exception as e:
            logger.error(f"Error sending message to user {user_id}: {e}")
            await self.remove_user(user_id)
            return False

    def get_room_state(self) -> Dict[str, Any]:
        """Get current room state for new joiners"""
        return {
            "artifact_id": self.artifact_id,
            "active_users": [
                {
                    "user_id": user_id,
                    "user_data": self.user_data.get(user_id, {}),
                    "cursor": self.cursors.get(user_id),
                    "selection": self.selections.get(user_id)
                }
                for user_id in self.connections.keys()
            ],
            "typing_users": list(self.typing_users),
            "last_activity": self.last_activity.isoformat()
        }


class WebSocketManager:
    """Manages WebSocket connections for real-time collaboration"""

    def __init__(self):
        self.rooms: Dict[str, CollaborationRoom] = {}  # artifact_id -> room
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> set of artifact_ids
        self.redis_client: Optional[redis.Redis] = None
        self.presence_tracker = PresenceTracker()
        self.notification_service = NotificationService()

    async def initialize(self):
        """Initialize the WebSocket manager with Redis connection"""
        try:
            if settings.REDIS_URL:
                self.redis_client = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    health_check_interval=30
                )
                await self.redis_client.ping()
                logger.info("WebSocket manager initialized with Redis")
            else:
                logger.warning("Redis not configured, using in-memory WebSocket management")
        except Exception as e:
            logger.error(f"Failed to initialize Redis for WebSocket manager: {e}")
            self.redis_client = None

    async def cleanup(self):
        """Cleanup WebSocket manager resources"""
        if self.redis_client:
            await self.redis_client.close()

    async def connect_user(self, websocket: WebSocket, user_id: str, artifact_id: str, user_data: Dict[str, Any]):
        """Connect a user to an artifact collaboration room"""
        await websocket.accept()

        # Create room if it doesn't exist
        if artifact_id not in self.rooms:
            self.rooms[artifact_id] = CollaborationRoom(artifact_id)

        room = self.rooms[artifact_id]

        # Add user to room
        await room.add_user(user_id, websocket, user_data)

        # Track user connections
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(artifact_id)

        # Update presence
        await self.presence_tracker.update_presence(user_id, artifact_id, "active")

        # Send current room state to the new user
        room_state = room.get_room_state()
        await room.send_to_user(user_id, {
            "type": "room_state",
            "data": room_state
        })

        logger.info(f"User {user_id} connected to artifact {artifact_id}")

        # Persist connection info in Redis if available
        if self.redis_client:
            await self._persist_connection(user_id, artifact_id, user_data)

    async def disconnect_user(self, user_id: str, artifact_id: str):
        """Disconnect a user from an artifact collaboration room"""
        if artifact_id in self.rooms:
            room = self.rooms[artifact_id]
            await room.remove_user(user_id)

            # Clean up empty rooms
            if not room.connections:
                del self.rooms[artifact_id]

        # Update user connections
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(artifact_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

        # Update presence
        await self.presence_tracker.update_presence(user_id, artifact_id, "offline")

        logger.info(f"User {user_id} disconnected from artifact {artifact_id}")

        # Remove connection info from Redis if available
        if self.redis_client:
            await self._remove_connection(user_id, artifact_id)

    async def handle_message(self, user_id: str, artifact_id: str, message: Dict[str, Any]):
        """Handle incoming WebSocket message"""
        if artifact_id not in self.rooms:
            return

        room = self.rooms[artifact_id]
        message_type = message.get("type")

        try:
            if message_type == MessageType.CURSOR_MOVE.value:
                await self._handle_cursor_move(room, user_id, message)
            elif message_type == MessageType.SELECTION_CHANGE.value:
                await self._handle_selection_change(room, user_id, message)
            elif message_type == MessageType.TYPING_START.value:
                await self._handle_typing_start(room, user_id, message)
            elif message_type == MessageType.TYPING_STOP.value:
                await self._handle_typing_stop(room, user_id, message)
            elif message_type == MessageType.ARTIFACT_EDIT.value:
                await self._handle_artifact_edit(room, user_id, message)
            elif message_type == MessageType.COMMENT_ADD.value:
                await self._handle_comment_add(room, user_id, message)
            elif message_type == MessageType.COMMENT_UPDATE.value:
                await self._handle_comment_update(room, user_id, message)
            elif message_type == MessageType.COMMENT_DELETE.value:
                await self._handle_comment_delete(room, user_id, message)
            else:
                logger.warning(f"Unknown message type: {message_type}")

        except Exception as e:
            logger.error(f"Error handling message {message_type} from user {user_id}: {e}")

    async def _handle_cursor_move(self, room: CollaborationRoom, user_id: str, message: Dict[str, Any]):
        """Handle cursor movement updates"""
        cursor_data = message.get("data", {})
        room.cursors[user_id] = cursor_data

        await room.broadcast_to_others(user_id, {
            "type": MessageType.CURSOR_MOVE.value,
            "user_id": user_id,
            "data": cursor_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    async def _handle_selection_change(self, room: CollaborationRoom, user_id: str, message: Dict[str, Any]):
        """Handle text selection changes"""
        selection_data = message.get("data", {})
        room.selections[user_id] = selection_data

        await room.broadcast_to_others(user_id, {
            "type": MessageType.SELECTION_CHANGE.value,
            "user_id": user_id,
            "data": selection_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    async def _handle_typing_start(self, room: CollaborationRoom, user_id: str, message: Dict[str, Any]):
        """Handle typing start notification"""
        room.typing_users.add(user_id)

        await room.broadcast_to_others(user_id, {
            "type": MessageType.TYPING_START.value,
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    async def _handle_typing_stop(self, room: CollaborationRoom, user_id: str, message: Dict[str, Any]):
        """Handle typing stop notification"""
        room.typing_users.discard(user_id)

        await room.broadcast_to_others(user_id, {
            "type": MessageType.TYPING_STOP.value,
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    async def _handle_artifact_edit(self, room: CollaborationRoom, user_id: str, message: Dict[str, Any]):
        """Handle artifact edit events"""
        edit_data = message.get("data", {})

        # Broadcast the edit to other users
        await room.broadcast_to_others(user_id, {
            "type": MessageType.ARTIFACT_EDIT.value,
            "user_id": user_id,
            "data": edit_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        # Log activity
        await self._log_activity(room.artifact_id, user_id, "artifact_edit", edit_data)

    async def _handle_comment_add(self, room: CollaborationRoom, user_id: str, message: Dict[str, Any]):
        """Handle new comment additions"""
        comment_data = message.get("data", {})

        # Broadcast the new comment to all users
        await room.broadcast_to_all({
            "type": MessageType.COMMENT_ADD.value,
            "user_id": user_id,
            "data": comment_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        # Log activity
        await self._log_activity(room.artifact_id, user_id, "comment_add", comment_data)

    async def _handle_comment_update(self, room: CollaborationRoom, user_id: str, message: Dict[str, Any]):
        """Handle comment updates"""
        comment_data = message.get("data", {})

        await room.broadcast_to_all({
            "type": MessageType.COMMENT_UPDATE.value,
            "user_id": user_id,
            "data": comment_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        # Log activity
        await self._log_activity(room.artifact_id, user_id, "comment_update", comment_data)

    async def _handle_comment_delete(self, room: CollaborationRoom, user_id: str, message: Dict[str, Any]):
        """Handle comment deletions"""
        comment_data = message.get("data", {})

        await room.broadcast_to_all({
            "type": MessageType.COMMENT_DELETE.value,
            "user_id": user_id,
            "data": comment_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        # Log activity
        await self._log_activity(room.artifact_id, user_id, "comment_delete", comment_data)

    async def _log_activity(self, artifact_id: str, user_id: str, activity_type: str, data: Dict[str, Any]):
        """Log collaboration activity to database"""
        try:
            async with AsyncSessionLocal() as session:
                from ..models import CollaborationActivity

                activity = CollaborationActivity(
                    id=str(uuid4()),
                    artifact_id=artifact_id,
                    user_id=user_id,
                    activity_type=activity_type,
                    data=data,
                    timestamp=datetime.now(timezone.utc)
                )

                session.add(activity)
                await session.commit()

        except Exception as e:
            logger.error(f"Failed to log activity: {e}")

    async def _persist_connection(self, user_id: str, artifact_id: str, user_data: Dict[str, Any]):
        """Persist connection info to Redis"""
        if not self.redis_client:
            return

        try:
            connection_key = f"collaboration:connection:{user_id}:{artifact_id}"
            await self.redis_client.hset(connection_key, mapping={
                "user_id": user_id,
                "artifact_id": artifact_id,
                "user_data": json.dumps(user_data),
                "connected_at": datetime.now(timezone.utc).isoformat()
            })
            await self.redis_client.expire(connection_key, 3600)  # 1 hour TTL

        except Exception as e:
            logger.error(f"Failed to persist connection to Redis: {e}")

    async def _remove_connection(self, user_id: str, artifact_id: str):
        """Remove connection info from Redis"""
        if not self.redis_client:
            return

        try:
            connection_key = f"collaboration:connection:{user_id}:{artifact_id}"
            await self.redis_client.delete(connection_key)

        except Exception as e:
            logger.error(f"Failed to remove connection from Redis: {e}")

    async def get_active_users(self, artifact_id: str) -> List[Dict[str, Any]]:
        """Get list of active users for an artifact"""
        if artifact_id not in self.rooms:
            return []

        room = self.rooms[artifact_id]
        return [
            {
                "user_id": user_id,
                "user_data": room.user_data.get(user_id, {}),
                "cursor": room.cursors.get(user_id),
                "selection": room.selections.get(user_id)
            }
            for user_id in room.connections.keys()
        ]

    async def send_notification(self, user_id: str, notification: Dict[str, Any]):
        """Send notification to a specific user across all their connections"""
        if user_id not in self.user_connections:
            return

        notification_message = {
            "type": MessageType.NOTIFICATION.value,
            "data": notification,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        for artifact_id in self.user_connections[user_id]:
            if artifact_id in self.rooms:
                room = self.rooms[artifact_id]
                await room.send_to_user(user_id, notification_message)


# Global WebSocket manager instance
websocket_manager = WebSocketManager()