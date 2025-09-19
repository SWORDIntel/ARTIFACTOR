-- Migration 002: Add collaboration tables for real-time collaboration features
-- ARTIFACTOR v3.0 Real-time collaboration database schema

-- Collaboration Comments Table
CREATE TABLE IF NOT EXISTS collaboration_comments (
    id VARCHAR PRIMARY KEY,
    artifact_id VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL REFERENCES users(id),
    parent_id VARCHAR REFERENCES collaboration_comments(id),

    -- Comment content
    content TEXT NOT NULL,
    content_type VARCHAR DEFAULT 'text',

    -- Position information for inline comments
    position_data JSONB,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    edited BOOLEAN DEFAULT FALSE,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_by VARCHAR REFERENCES users(id),
    resolved_at TIMESTAMPTZ,

    -- Reactions and engagement
    reactions JSONB DEFAULT '{}',
    mentions JSONB DEFAULT '[]'
);

-- Collaboration Activities Table
CREATE TABLE IF NOT EXISTS collaboration_activities (
    id VARCHAR PRIMARY KEY,
    artifact_id VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL REFERENCES users(id),

    -- Activity details
    activity_type VARCHAR NOT NULL,
    activity_category VARCHAR NOT NULL DEFAULT 'general',
    description TEXT,

    -- Activity data
    data JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    timestamp TIMESTAMPTZ DEFAULT NOW(),

    -- Visibility and filtering
    visibility VARCHAR DEFAULT 'public',
    tags JSONB DEFAULT '[]',

    -- Related entities
    related_comment_id VARCHAR REFERENCES collaboration_comments(id),
    related_user_id VARCHAR REFERENCES users(id)
);

-- User Presence Table
CREATE TABLE IF NOT EXISTS user_presence (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL REFERENCES users(id),
    artifact_id VARCHAR NOT NULL,

    -- Presence status
    status VARCHAR NOT NULL DEFAULT 'active',
    activity VARCHAR,

    -- Location information
    cursor_position JSONB,
    viewport JSONB,

    -- Timestamps
    last_seen TIMESTAMPTZ DEFAULT NOW(),
    joined_at TIMESTAMPTZ DEFAULT NOW(),

    -- Connection info
    session_id VARCHAR,
    connection_info JSONB DEFAULT '{}'
);

-- Collaboration Notifications Table
CREATE TABLE IF NOT EXISTS collaboration_notifications (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL REFERENCES users(id),
    artifact_id VARCHAR,

    -- Notification details
    type VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    message TEXT NOT NULL,

    -- Related entities
    related_user_id VARCHAR REFERENCES users(id),
    related_comment_id VARCHAR REFERENCES collaboration_comments(id),
    related_activity_id VARCHAR REFERENCES collaboration_activities(id),

    -- Status
    read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMPTZ,
    priority VARCHAR DEFAULT 'normal',

    -- Delivery
    delivery_channels JSONB DEFAULT '[]',
    delivered_channels JSONB DEFAULT '[]',

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    scheduled_for TIMESTAMPTZ,

    -- Metadata
    data JSONB DEFAULT '{}'
);

-- Collaboration Workspaces Table
CREATE TABLE IF NOT EXISTS collaboration_workspaces (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    description TEXT,

    -- Workspace settings
    settings JSONB DEFAULT '{}',
    features JSONB DEFAULT '[]',

    -- Access control
    visibility VARCHAR DEFAULT 'private',
    default_role VARCHAR DEFAULT 'viewer',

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR NOT NULL REFERENCES users(id),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Stats
    member_count INTEGER DEFAULT 0,
    artifact_count INTEGER DEFAULT 0
);

-- Workspace Memberships Table
CREATE TABLE IF NOT EXISTS workspace_memberships (
    id VARCHAR PRIMARY KEY,
    workspace_id VARCHAR NOT NULL REFERENCES collaboration_workspaces(id),
    user_id VARCHAR NOT NULL REFERENCES users(id),

    -- Role and permissions
    role VARCHAR NOT NULL,
    permissions JSONB DEFAULT '[]',

    -- Membership details
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    invited_by VARCHAR REFERENCES users(id),
    status VARCHAR DEFAULT 'active',

    -- Settings
    notification_preferences JSONB DEFAULT '{}'
);

-- Artifact Collaboration Settings Table
CREATE TABLE IF NOT EXISTS artifact_collaboration (
    id VARCHAR PRIMARY KEY,
    artifact_id VARCHAR NOT NULL UNIQUE,
    workspace_id VARCHAR REFERENCES collaboration_workspaces(id),

    -- Collaboration settings
    collaboration_enabled BOOLEAN DEFAULT TRUE,
    real_time_editing BOOLEAN DEFAULT TRUE,
    comments_enabled BOOLEAN DEFAULT TRUE,
    activity_tracking BOOLEAN DEFAULT TRUE,

    -- Access control
    access_level VARCHAR DEFAULT 'workspace',
    allowed_users JSONB DEFAULT '[]',

    -- Permissions
    edit_permissions JSONB DEFAULT '{}',
    comment_permissions JSONB DEFAULT '{}',

    -- Settings
    conflict_resolution VARCHAR DEFAULT 'last_write_wins',
    version_control BOOLEAN DEFAULT TRUE,
    auto_save_interval INTEGER DEFAULT 30,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Collaboration Versions Table
CREATE TABLE IF NOT EXISTS collaboration_versions (
    id VARCHAR PRIMARY KEY,
    artifact_id VARCHAR NOT NULL,
    version_number INTEGER NOT NULL,

    -- Version details
    content TEXT,
    changes JSONB DEFAULT '{}',
    change_summary TEXT,

    -- Author information
    created_by VARCHAR NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Version metadata
    tags JSONB DEFAULT '[]',
    branch VARCHAR DEFAULT 'main',
    parent_version_id VARCHAR REFERENCES collaboration_versions(id),

    -- Conflicts and resolution
    has_conflicts BOOLEAN DEFAULT FALSE,
    conflict_resolution JSONB DEFAULT '{}'
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_comment_artifact_created ON collaboration_comments(artifact_id, created_at);
CREATE INDEX IF NOT EXISTS idx_comment_user_created ON collaboration_comments(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_comment_parent ON collaboration_comments(parent_id);

CREATE INDEX IF NOT EXISTS idx_activity_artifact_timestamp ON collaboration_activities(artifact_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_activity_user_timestamp ON collaboration_activities(user_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_activity_type_timestamp ON collaboration_activities(activity_type, timestamp);
CREATE INDEX IF NOT EXISTS idx_activity_category ON collaboration_activities(activity_category);

CREATE INDEX IF NOT EXISTS idx_presence_user_artifact ON user_presence(user_id, artifact_id);
CREATE INDEX IF NOT EXISTS idx_presence_artifact_status ON user_presence(artifact_id, status);
CREATE INDEX IF NOT EXISTS idx_presence_last_seen ON user_presence(last_seen);

CREATE INDEX IF NOT EXISTS idx_notification_user_created ON collaboration_notifications(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_notification_user_read ON collaboration_notifications(user_id, read);
CREATE INDEX IF NOT EXISTS idx_notification_artifact ON collaboration_notifications(artifact_id);
CREATE INDEX IF NOT EXISTS idx_notification_type ON collaboration_notifications(type);

CREATE INDEX IF NOT EXISTS idx_workspace_creator ON collaboration_workspaces(created_by);
CREATE INDEX IF NOT EXISTS idx_workspace_created ON collaboration_workspaces(created_at);

CREATE INDEX IF NOT EXISTS idx_membership_workspace_user ON workspace_memberships(workspace_id, user_id);
CREATE INDEX IF NOT EXISTS idx_membership_user ON workspace_memberships(user_id);
CREATE INDEX IF NOT EXISTS idx_membership_workspace ON workspace_memberships(workspace_id);

CREATE INDEX IF NOT EXISTS idx_artifact_collab_artifact ON artifact_collaboration(artifact_id);
CREATE INDEX IF NOT EXISTS idx_artifact_collab_workspace ON artifact_collaboration(workspace_id);

CREATE INDEX IF NOT EXISTS idx_version_artifact_number ON collaboration_versions(artifact_id, version_number);
CREATE INDEX IF NOT EXISTS idx_version_author_created ON collaboration_versions(created_by, created_at);
CREATE INDEX IF NOT EXISTS idx_version_artifact_created ON collaboration_versions(artifact_id, created_at);

-- Add triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_collaboration_comments_updated_at BEFORE UPDATE ON collaboration_comments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_collaboration_workspaces_updated_at BEFORE UPDATE ON collaboration_workspaces
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_artifact_collaboration_updated_at BEFORE UPDATE ON artifact_collaboration
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();