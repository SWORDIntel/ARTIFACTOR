-- ARTIFACTOR v3.0 Database Initialization
-- PostgreSQL database schema for enterprise artifact management

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "citext";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Set timezone
SET timezone = 'UTC';

-- =====================================
-- USERS AND AUTHENTICATION
-- =====================================

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email CITEXT UNIQUE NOT NULL,
    username VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    hashed_password VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    is_verified BOOLEAN DEFAULT FALSE,
    avatar_url TEXT,
    bio TEXT,
    location VARCHAR(255),
    website VARCHAR(255),
    github_id VARCHAR(255) UNIQUE,
    github_username VARCHAR(255),
    github_access_token TEXT,
    last_login_at TIMESTAMP WITH TIME ZONE,
    email_verified_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User sessions
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    refresh_token VARCHAR(255) UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================
-- ARTIFACTS
-- =====================================

CREATE TYPE artifact_type AS ENUM (
    'code', 'document', 'image', 'data', 'config', 'notebook', 'other'
);

CREATE TYPE artifact_status AS ENUM (
    'draft', 'published', 'archived', 'deleted'
);

CREATE TABLE IF NOT EXISTS artifacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    content TEXT,
    file_path VARCHAR(500),
    file_name VARCHAR(255),
    file_size BIGINT,
    mime_type VARCHAR(255),
    language VARCHAR(100),
    artifact_type artifact_type DEFAULT 'other',
    status artifact_status DEFAULT 'draft',
    is_public BOOLEAN DEFAULT FALSE,

    -- Ownership
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Source information
    source_url TEXT,
    claude_conversation_id VARCHAR(255),
    claude_artifact_id VARCHAR(255),

    -- Classification and tagging
    tags TEXT[],
    category VARCHAR(100),
    confidence_score REAL,

    -- Search and indexing
    search_vector TSVECTOR,
    embedding VECTOR(384),

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    published_at TIMESTAMP WITH TIME ZONE,
    archived_at TIMESTAMP WITH TIME ZONE
);

-- Artifact versions for history tracking
CREATE TABLE IF NOT EXISTS artifact_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    artifact_id UUID NOT NULL REFERENCES artifacts(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    content TEXT,
    changes_summary TEXT,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(artifact_id, version_number)
);

-- =====================================
-- COLLABORATION
-- =====================================

CREATE TYPE collaboration_role AS ENUM ('viewer', 'editor', 'admin');

CREATE TABLE IF NOT EXISTS artifact_collaborators (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    artifact_id UUID NOT NULL REFERENCES artifacts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role collaboration_role DEFAULT 'viewer',
    invited_by UUID REFERENCES users(id),
    invited_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    accepted_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(artifact_id, user_id)
);

-- Comments and discussions
CREATE TABLE IF NOT EXISTS artifact_comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    artifact_id UUID NOT NULL REFERENCES artifacts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES artifact_comments(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    line_number INTEGER,
    position_start INTEGER,
    position_end INTEGER,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_by UUID REFERENCES users(id),
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Real-time collaboration sessions
CREATE TABLE IF NOT EXISTS collaboration_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    artifact_id UUID NOT NULL REFERENCES artifacts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR(255) NOT NULL,
    cursor_position INTEGER,
    selection_start INTEGER,
    selection_end INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================
-- MACHINE LEARNING
-- =====================================

CREATE TABLE IF NOT EXISTS ml_models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    model_type VARCHAR(100) NOT NULL, -- 'classification', 'embeddings', 'search'
    version VARCHAR(50) NOT NULL,
    model_path VARCHAR(500),
    config JSONB DEFAULT '{}',
    metrics JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    trained_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ML predictions and classifications
CREATE TABLE IF NOT EXISTS ml_predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    artifact_id UUID NOT NULL REFERENCES artifacts(id) ON DELETE CASCADE,
    model_id UUID NOT NULL REFERENCES ml_models(id),
    prediction_type VARCHAR(100) NOT NULL,
    prediction_value TEXT NOT NULL,
    confidence_score REAL NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Search index for vector similarity
CREATE TABLE IF NOT EXISTS search_index (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    artifact_id UUID NOT NULL REFERENCES artifacts(id) ON DELETE CASCADE,
    content_hash VARCHAR(64) NOT NULL,
    embedding VECTOR(384) NOT NULL,
    content_preview TEXT,
    indexed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================
-- PLUGINS AND EXTENSIONS
-- =====================================

CREATE TYPE plugin_status AS ENUM ('active', 'inactive', 'disabled', 'error');

CREATE TABLE IF NOT EXISTS plugins (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    version VARCHAR(50) NOT NULL,
    author VARCHAR(255),
    homepage VARCHAR(500),
    repository VARCHAR(500),
    license VARCHAR(100),
    status plugin_status DEFAULT 'inactive',
    config JSONB DEFAULT '{}',
    permissions TEXT[],
    install_path VARCHAR(500),
    checksum VARCHAR(64),
    installed_by UUID REFERENCES users(id),
    installed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Plugin execution logs
CREATE TABLE IF NOT EXISTS plugin_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plugin_id UUID NOT NULL REFERENCES plugins(id) ON DELETE CASCADE,
    artifact_id UUID REFERENCES artifacts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action VARCHAR(255) NOT NULL,
    input_data JSONB,
    output_data JSONB,
    status VARCHAR(50) NOT NULL, -- 'success', 'error', 'timeout'
    error_message TEXT,
    execution_time_ms INTEGER,
    memory_usage_mb INTEGER,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- =====================================
-- SYSTEM AND ANALYTICS
-- =====================================

-- User activity tracking
CREATE TABLE IF NOT EXISTS user_activities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    activity_type VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100), -- 'artifact', 'comment', 'plugin', etc.
    entity_id UUID,
    metadata JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- System notifications
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    notification_type VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100),
    entity_id UUID,
    is_read BOOLEAN DEFAULT FALSE,
    is_email_sent BOOLEAN DEFAULT FALSE,
    data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    read_at TIMESTAMP WITH TIME ZONE
);

-- System configuration
CREATE TABLE IF NOT EXISTS system_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    config_key VARCHAR(255) UNIQUE NOT NULL,
    config_value TEXT,
    config_type VARCHAR(50) DEFAULT 'string', -- 'string', 'integer', 'boolean', 'json'
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================
-- INDEXES FOR PERFORMANCE
-- =====================================

-- Users indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_github_id ON users(github_id);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- User sessions indexes
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON user_sessions(is_active);

-- Artifacts indexes
CREATE INDEX IF NOT EXISTS idx_artifacts_owner_id ON artifacts(owner_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_status ON artifacts(status);
CREATE INDEX IF NOT EXISTS idx_artifacts_type ON artifacts(artifact_type);
CREATE INDEX IF NOT EXISTS idx_artifacts_public ON artifacts(is_public);
CREATE INDEX IF NOT EXISTS idx_artifacts_language ON artifacts(language);
CREATE INDEX IF NOT EXISTS idx_artifacts_category ON artifacts(category);
CREATE INDEX IF NOT EXISTS idx_artifacts_created_at ON artifacts(created_at);
CREATE INDEX IF NOT EXISTS idx_artifacts_updated_at ON artifacts(updated_at);
CREATE INDEX IF NOT EXISTS idx_artifacts_tags ON artifacts USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_artifacts_search_vector ON artifacts USING GIN(search_vector);
CREATE INDEX IF NOT EXISTS idx_artifacts_claude_conversation ON artifacts(claude_conversation_id);

-- Vector similarity index for embeddings
CREATE INDEX IF NOT EXISTS idx_artifacts_embedding ON artifacts USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Collaboration indexes
CREATE INDEX IF NOT EXISTS idx_artifact_collaborators_artifact_id ON artifact_collaborators(artifact_id);
CREATE INDEX IF NOT EXISTS idx_artifact_collaborators_user_id ON artifact_collaborators(user_id);

-- Comments indexes
CREATE INDEX IF NOT EXISTS idx_artifact_comments_artifact_id ON artifact_comments(artifact_id);
CREATE INDEX IF NOT EXISTS idx_artifact_comments_user_id ON artifact_comments(user_id);
CREATE INDEX IF NOT EXISTS idx_artifact_comments_parent_id ON artifact_comments(parent_id);
CREATE INDEX IF NOT EXISTS idx_artifact_comments_created_at ON artifact_comments(created_at);

-- ML indexes
CREATE INDEX IF NOT EXISTS idx_ml_predictions_artifact_id ON ml_predictions(artifact_id);
CREATE INDEX IF NOT EXISTS idx_ml_predictions_model_id ON ml_predictions(model_id);
CREATE INDEX IF NOT EXISTS idx_search_index_artifact_id ON search_index(artifact_id);
CREATE INDEX IF NOT EXISTS idx_search_index_embedding ON search_index USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Plugin indexes
CREATE INDEX IF NOT EXISTS idx_plugins_status ON plugins(status);
CREATE INDEX IF NOT EXISTS idx_plugin_executions_plugin_id ON plugin_executions(plugin_id);
CREATE INDEX IF NOT EXISTS idx_plugin_executions_user_id ON plugin_executions(user_id);
CREATE INDEX IF NOT EXISTS idx_plugin_executions_started_at ON plugin_executions(started_at);

-- Activity indexes
CREATE INDEX IF NOT EXISTS idx_user_activities_user_id ON user_activities(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activities_type ON user_activities(activity_type);
CREATE INDEX IF NOT EXISTS idx_user_activities_created_at ON user_activities(created_at);

-- Notifications indexes
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at);

-- =====================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- =====================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to tables with updated_at column
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_sessions_updated_at BEFORE UPDATE ON user_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_artifacts_updated_at BEFORE UPDATE ON artifacts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_artifact_comments_updated_at BEFORE UPDATE ON artifact_comments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_ml_models_updated_at BEFORE UPDATE ON ml_models FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_plugins_updated_at BEFORE UPDATE ON plugins FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_system_config_updated_at BEFORE UPDATE ON system_config FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to update search vector
CREATE OR REPLACE FUNCTION update_artifact_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := to_tsvector('english',
        COALESCE(NEW.title, '') || ' ' ||
        COALESCE(NEW.description, '') || ' ' ||
        COALESCE(NEW.content, '') || ' ' ||
        COALESCE(array_to_string(NEW.tags, ' '), '')
    );
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply search vector trigger
CREATE TRIGGER update_artifacts_search_vector
    BEFORE INSERT OR UPDATE ON artifacts
    FOR EACH ROW EXECUTE FUNCTION update_artifact_search_vector();

-- =====================================
-- INITIAL DATA
-- =====================================

-- Insert default ML models
INSERT INTO ml_models (name, description, model_type, version, is_active) VALUES
('sentence-transformers/all-MiniLM-L6-v2', 'General purpose sentence embeddings', 'embeddings', '1.0.0', true),
('artifact-classifier-v1', 'Artifact type classification model', 'classification', '1.0.0', true),
('code-language-detector', 'Programming language detection', 'classification', '1.0.0', true)
ON CONFLICT (name) DO NOTHING;

-- Insert default system configuration
INSERT INTO system_config (config_key, config_value, config_type, description, is_public) VALUES
('app_name', 'ARTIFACTOR', 'string', 'Application name', true),
('app_version', '3.0.0', 'string', 'Application version', true),
('max_upload_size', '104857600', 'integer', 'Maximum upload size in bytes (100MB)', false),
('enable_ml_classification', 'true', 'boolean', 'Enable ML-powered classification', false),
('enable_semantic_search', 'true', 'boolean', 'Enable semantic search', false),
('default_artifact_status', 'draft', 'string', 'Default status for new artifacts', false),
('email_notifications_enabled', 'true', 'boolean', 'Enable email notifications', false)
ON CONFLICT (config_key) DO NOTHING;

-- Create default admin user (update credentials in production!)
INSERT INTO users (
    email,
    username,
    full_name,
    hashed_password,
    is_active,
    is_superuser,
    is_verified
) VALUES (
    'admin@artifactor.local',
    'admin',
    'System Administrator',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewvhOKoHn8E2yJ4y', -- password: admin123
    true,
    true,
    true
) ON CONFLICT (email) DO NOTHING;

-- =====================================
-- PERMISSIONS
-- =====================================

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO artifactor;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO artifactor;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO artifactor;

-- Create read-only user for monitoring/reporting
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'artifactor_readonly') THEN
        CREATE ROLE artifactor_readonly WITH LOGIN PASSWORD 'readonly123';
    END IF;
END
$$;

GRANT CONNECT ON DATABASE artifactor TO artifactor_readonly;
GRANT USAGE ON SCHEMA public TO artifactor_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO artifactor_readonly;

-- =====================================
-- VIEWS FOR COMMON QUERIES
-- =====================================

-- View for public artifacts with owner information
CREATE OR REPLACE VIEW public_artifacts AS
SELECT
    a.*,
    u.username as owner_username,
    u.full_name as owner_full_name,
    u.avatar_url as owner_avatar_url
FROM artifacts a
JOIN users u ON a.owner_id = u.id
WHERE a.is_public = true AND a.status = 'published';

-- View for artifact statistics
CREATE OR REPLACE VIEW artifact_stats AS
SELECT
    COUNT(*) as total_artifacts,
    COUNT(*) FILTER (WHERE status = 'published') as published_artifacts,
    COUNT(*) FILTER (WHERE is_public = true) as public_artifacts,
    COUNT(DISTINCT owner_id) as unique_owners,
    COUNT(DISTINCT artifact_type) as unique_types,
    AVG(file_size) as avg_file_size,
    MAX(created_at) as latest_artifact
FROM artifacts;

-- View for user statistics
CREATE OR REPLACE VIEW user_stats AS
SELECT
    COUNT(*) as total_users,
    COUNT(*) FILTER (WHERE is_active = true) as active_users,
    COUNT(*) FILTER (WHERE is_verified = true) as verified_users,
    COUNT(*) FILTER (WHERE github_id IS NOT NULL) as github_users,
    MAX(created_at) as latest_registration
FROM users;

COMMIT;