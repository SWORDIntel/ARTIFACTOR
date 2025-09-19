"""
Database models for real-time collaboration features in ARTIFACTOR v3.0
Includes comments, activity tracking, presence, and notifications
"""

from sqlalchemy import Column, String, DateTime, Text, JSON, Boolean, ForeignKey, Integer, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
from uuid import uuid4

from ..database import Base


class CollaborationComment(Base):
    """Model for threaded comments on artifacts"""
    __tablename__ = "collaboration_comments"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    artifact_id = Column(String, nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    parent_id = Column(String, ForeignKey("collaboration_comments.id"), nullable=True)

    # Comment content
    content = Column(Text, nullable=False)
    content_type = Column(String, default="text")  # text, markdown, html

    # Position information for inline comments
    position_data = Column(JSON, nullable=True)  # line number, character position, etc.

    # Metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    edited = Column(Boolean, default=False)
    resolved = Column(Boolean, default=False)
    resolved_by = Column(String, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Reactions and engagement
    reactions = Column(JSON, default=dict)  # {"👍": ["user1", "user2"], "👎": ["user3"]}
    mentions = Column(JSON, default=list)  # ["@user1", "@user2"]

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    resolver = relationship("User", foreign_keys=[resolved_by])
    replies = relationship("CollaborationComment", backref="parent", remote_side=[id])

    # Indexes
    __table_args__ = (
        Index("idx_comment_artifact_created", "artifact_id", "created_at"),
        Index("idx_comment_user_created", "user_id", "created_at"),
        Index("idx_comment_parent", "parent_id"),
    )


class CollaborationActivity(Base):
    """Model for tracking all collaboration activities"""
    __tablename__ = "collaboration_activities"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    artifact_id = Column(String, nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Activity details
    activity_type = Column(String, nullable=False)  # edit, comment, join, leave, etc.
    activity_category = Column(String, nullable=False, default="general")  # edit, comment, collaboration, system
    description = Column(Text, nullable=True)

    # Activity data
    data = Column(JSON, default=dict)  # activity-specific data
    metadata = Column(JSON, default=dict)  # additional metadata

    # Timestamps
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Visibility and filtering
    visibility = Column(String, default="public")  # public, private, team
    tags = Column(JSON, default=list)  # ["important", "bug-fix", etc.]

    # Related entities
    related_comment_id = Column(String, ForeignKey("collaboration_comments.id"), nullable=True)
    related_user_id = Column(String, ForeignKey("users.id"), nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    related_user = relationship("User", foreign_keys=[related_user_id])
    related_comment = relationship("CollaborationComment")

    # Indexes
    __table_args__ = (
        Index("idx_activity_artifact_timestamp", "artifact_id", "timestamp"),
        Index("idx_activity_user_timestamp", "user_id", "timestamp"),
        Index("idx_activity_type_timestamp", "activity_type", "timestamp"),
        Index("idx_activity_category", "activity_category"),
    )


class UserPresence(Base):
    """Model for tracking user presence in real-time"""
    __tablename__ = "user_presence"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    artifact_id = Column(String, nullable=False)

    # Presence status
    status = Column(String, nullable=False, default="active")  # active, away, offline
    activity = Column(String, nullable=True)  # typing, editing, viewing, etc.

    # Location information
    cursor_position = Column(JSON, nullable=True)  # line, column, selection
    viewport = Column(JSON, nullable=True)  # visible area information

    # Timestamps
    last_seen = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    joined_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Connection info
    session_id = Column(String, nullable=True)
    connection_info = Column(JSON, default=dict)  # browser, device, etc.

    # Relationships
    user = relationship("User")

    # Indexes
    __table_args__ = (
        Index("idx_presence_user_artifact", "user_id", "artifact_id"),
        Index("idx_presence_artifact_status", "artifact_id", "status"),
        Index("idx_presence_last_seen", "last_seen"),
    )


class CollaborationNotification(Base):
    """Model for collaboration notifications"""
    __tablename__ = "collaboration_notifications"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    artifact_id = Column(String, nullable=False)

    # Notification details
    type = Column(String, nullable=False)  # mention, comment_reply, artifact_update, etc.
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)

    # Related entities
    related_user_id = Column(String, ForeignKey("users.id"), nullable=True)  # who triggered the notification
    related_comment_id = Column(String, ForeignKey("collaboration_comments.id"), nullable=True)
    related_activity_id = Column(String, ForeignKey("collaboration_activities.id"), nullable=True)

    # Status
    read = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True), nullable=True)
    priority = Column(String, default="normal")  # low, normal, high, urgent

    # Delivery
    delivery_channels = Column(JSON, default=list)  # ["websocket", "email", "push"]
    delivered_channels = Column(JSON, default=list)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    scheduled_for = Column(DateTime(timezone=True), nullable=True)  # for delayed notifications

    # Metadata
    data = Column(JSON, default=dict)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    related_user = relationship("User", foreign_keys=[related_user_id])
    related_comment = relationship("CollaborationComment")
    related_activity = relationship("CollaborationActivity")

    # Indexes
    __table_args__ = (
        Index("idx_notification_user_created", "user_id", "created_at"),
        Index("idx_notification_user_read", "user_id", "read"),
        Index("idx_notification_artifact", "artifact_id"),
        Index("idx_notification_type", "type"),
    )


class CollaborationWorkspace(Base):
    """Model for team workspaces with role-based access"""
    __tablename__ = "collaboration_workspaces"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Workspace settings
    settings = Column(JSON, default=dict)
    features = Column(JSON, default=list)  # enabled features

    # Access control
    visibility = Column(String, default="private")  # public, private, invite_only
    default_role = Column(String, default="viewer")  # owner, admin, editor, viewer

    # Metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Stats
    member_count = Column(Integer, default=0)
    artifact_count = Column(Integer, default=0)

    # Relationships
    creator = relationship("User")

    # Indexes
    __table_args__ = (
        Index("idx_workspace_creator", "created_by"),
        Index("idx_workspace_created", "created_at"),
    )


class WorkspaceMembership(Base):
    """Model for workspace memberships and roles"""
    __tablename__ = "workspace_memberships"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    workspace_id = Column(String, ForeignKey("collaboration_workspaces.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Role and permissions
    role = Column(String, nullable=False)  # owner, admin, editor, viewer
    permissions = Column(JSON, default=list)  # custom permissions

    # Membership details
    joined_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    invited_by = Column(String, ForeignKey("users.id"), nullable=True)
    status = Column(String, default="active")  # active, inactive, pending

    # Settings
    notification_preferences = Column(JSON, default=dict)

    # Relationships
    workspace = relationship("CollaborationWorkspace")
    user = relationship("User", foreign_keys=[user_id])
    inviter = relationship("User", foreign_keys=[invited_by])

    # Indexes
    __table_args__ = (
        Index("idx_membership_workspace_user", "workspace_id", "user_id"),
        Index("idx_membership_user", "user_id"),
        Index("idx_membership_workspace", "workspace_id"),
    )


class ArtifactCollaboration(Base):
    """Model for artifact-specific collaboration settings"""
    __tablename__ = "artifact_collaboration"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    artifact_id = Column(String, nullable=False, unique=True)
    workspace_id = Column(String, ForeignKey("collaboration_workspaces.id"), nullable=True)

    # Collaboration settings
    collaboration_enabled = Column(Boolean, default=True)
    real_time_editing = Column(Boolean, default=True)
    comments_enabled = Column(Boolean, default=True)
    activity_tracking = Column(Boolean, default=True)

    # Access control
    access_level = Column(String, default="workspace")  # public, workspace, private, custom
    allowed_users = Column(JSON, default=list)  # for custom access

    # Permissions
    edit_permissions = Column(JSON, default=dict)  # role-based edit permissions
    comment_permissions = Column(JSON, default=dict)  # role-based comment permissions

    # Settings
    conflict_resolution = Column(String, default="last_write_wins")  # last_write_wins, manual_merge
    version_control = Column(Boolean, default=True)
    auto_save_interval = Column(Integer, default=30)  # seconds

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    workspace = relationship("CollaborationWorkspace")

    # Indexes
    __table_args__ = (
        Index("idx_artifact_collab_artifact", "artifact_id"),
        Index("idx_artifact_collab_workspace", "workspace_id"),
    )


class CollaborationVersion(Base):
    """Model for tracking artifact versions during collaboration"""
    __tablename__ = "collaboration_versions"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    artifact_id = Column(String, nullable=False)
    version_number = Column(Integer, nullable=False)

    # Version details
    content = Column(Text, nullable=True)  # snapshot of content
    changes = Column(JSON, default=dict)  # diff information
    change_summary = Column(Text, nullable=True)

    # Author information
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Version metadata
    tags = Column(JSON, default=list)  # ["major", "minor", "hotfix"]
    branch = Column(String, default="main")
    parent_version_id = Column(String, ForeignKey("collaboration_versions.id"), nullable=True)

    # Conflicts and resolution
    has_conflicts = Column(Boolean, default=False)
    conflict_resolution = Column(JSON, default=dict)

    # Relationships
    author = relationship("User")
    parent_version = relationship("CollaborationVersion", remote_side=[id])

    # Indexes
    __table_args__ = (
        Index("idx_version_artifact_number", "artifact_id", "version_number"),
        Index("idx_version_author_created", "created_by", "created_at"),
        Index("idx_version_artifact_created", "artifact_id", "created_at"),
    )