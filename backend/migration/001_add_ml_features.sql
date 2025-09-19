-- ARTIFACTOR v3.0 ML Features Migration
-- Add ML classification, semantic search, and smart tagging capabilities

-- ML Classification results table
CREATE TABLE ml_classifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artifact_id UUID NOT NULL REFERENCES artifacts(id) ON DELETE CASCADE,

    -- Classification results
    predicted_language VARCHAR(50),
    language_confidence FLOAT,
    content_type VARCHAR(50),
    content_type_confidence FLOAT,
    project_category VARCHAR(100),
    project_category_confidence FLOAT,
    quality_assessment VARCHAR(20),
    quality_confidence FLOAT,

    -- Processing metadata
    classification_version VARCHAR(20) DEFAULT '1.0',
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Full classification data (JSON)
    full_results JSONB DEFAULT '{}'::jsonb
);

-- Artifact embeddings for semantic search
CREATE TABLE artifact_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artifact_id UUID NOT NULL UNIQUE REFERENCES artifacts(id) ON DELETE CASCADE,

    -- Embedding data
    embedding_vector FLOAT[] NOT NULL, -- 384-dimensional vector
    embedding_model VARCHAR(100) DEFAULT 'all-MiniLM-L6-v2',
    embedding_version VARCHAR(20) DEFAULT '1.0',

    -- Metadata for embedding generation
    content_hash VARCHAR(64), -- SHA-256 of content used
    text_processed TEXT, -- Preprocessed text used for embedding
    processing_time_ms INTEGER,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Search query logging and analytics
CREATE TABLE search_queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_text TEXT NOT NULL,
    search_type VARCHAR(20) NOT NULL, -- semantic, keyword, hybrid

    -- User and session info
    user_id UUID REFERENCES users(id),
    session_id VARCHAR(255),
    ip_address VARCHAR(45),

    -- Query processing
    processed_query JSONB DEFAULT '{}'::jsonb,
    filters_applied JSONB DEFAULT '{}'::jsonb,
    results_count INTEGER DEFAULT 0,
    response_time_ms INTEGER,

    -- Results interaction
    clicked_results TEXT[], -- Artifact IDs that were clicked
    no_results BOOLEAN DEFAULT FALSE,
    user_satisfied BOOLEAN, -- User feedback if available

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ML model performance metrics and monitoring
CREATE TABLE ml_model_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(20) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,

    -- Context
    evaluation_context JSONB DEFAULT '{}'::jsonb, -- Test set info, conditions, etc.
    sample_size INTEGER,

    -- Timestamps
    measured_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Smart tag suggestions and user feedback
CREATE TABLE tag_suggestions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artifact_id UUID NOT NULL REFERENCES artifacts(id) ON DELETE CASCADE,

    -- Suggestion details
    suggested_tag VARCHAR(100) NOT NULL,
    confidence_score FLOAT NOT NULL,
    suggestion_source VARCHAR(50) NOT NULL, -- technology_analysis, nlp, etc.

    -- User feedback
    user_accepted BOOLEAN, -- Did user accept the suggestion?
    user_feedback VARCHAR(500), -- Optional feedback
    feedback_timestamp TIMESTAMP WITH TIME ZONE,

    -- Suggestion metadata
    suggestion_context JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance optimization
CREATE INDEX idx_ml_classifications_artifact ON ml_classifications(artifact_id);
CREATE INDEX idx_ml_classifications_language ON ml_classifications(predicted_language);
CREATE INDEX idx_ml_classifications_content_type ON ml_classifications(content_type);
CREATE INDEX idx_ml_classifications_category ON ml_classifications(project_category);
CREATE INDEX idx_ml_classifications_created ON ml_classifications(created_at DESC);

CREATE INDEX idx_artifact_embeddings_artifact ON artifact_embeddings(artifact_id);
CREATE INDEX idx_artifact_embeddings_hash ON artifact_embeddings(content_hash);
CREATE INDEX idx_artifact_embeddings_model ON artifact_embeddings(embedding_model);

CREATE INDEX idx_search_queries_user_time ON search_queries(user_id, created_at DESC);
CREATE INDEX idx_search_queries_text ON search_queries USING gin(to_tsvector('english', query_text));
CREATE INDEX idx_search_queries_type_time ON search_queries(search_type, created_at DESC);
CREATE INDEX idx_search_queries_results ON search_queries(results_count);

CREATE INDEX idx_ml_model_metrics_model_time ON ml_model_metrics(model_name, measured_at DESC);
CREATE INDEX idx_ml_model_metrics_metric ON ml_model_metrics(metric_name);

CREATE INDEX idx_tag_suggestions_artifact ON tag_suggestions(artifact_id);
CREATE INDEX idx_tag_suggestions_tag ON tag_suggestions(suggested_tag);
CREATE INDEX idx_tag_suggestions_feedback ON tag_suggestions(user_accepted);
CREATE INDEX idx_tag_suggestions_source ON tag_suggestions(suggestion_source);
CREATE INDEX idx_tag_suggestions_created ON tag_suggestions(created_at DESC);

-- Add triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_ml_classifications_updated_at
    BEFORE UPDATE ON ml_classifications
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_artifact_embeddings_updated_at
    BEFORE UPDATE ON artifact_embeddings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add comment for documentation
COMMENT ON TABLE ml_classifications IS 'ML classification results for artifacts including language detection, content type, and quality assessment';
COMMENT ON TABLE artifact_embeddings IS 'Vector embeddings for semantic search functionality';
COMMENT ON TABLE search_queries IS 'Search query logging for analytics and performance monitoring';
COMMENT ON TABLE ml_model_metrics IS 'ML model performance metrics and monitoring data';
COMMENT ON TABLE tag_suggestions IS 'Smart tag suggestions with user feedback tracking';

-- Create view for ML analytics
CREATE VIEW ml_classification_summary AS
SELECT
    predicted_language,
    content_type,
    project_category,
    quality_assessment,
    COUNT(*) as count,
    AVG(language_confidence) as avg_language_confidence,
    AVG(content_type_confidence) as avg_content_confidence,
    AVG(project_category_confidence) as avg_category_confidence,
    AVG(processing_time_ms) as avg_processing_time
FROM ml_classifications
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY predicted_language, content_type, project_category, quality_assessment
ORDER BY count DESC;

-- Create view for search analytics
CREATE VIEW search_analytics_summary AS
SELECT
    search_type,
    DATE_TRUNC('day', created_at) as search_date,
    COUNT(*) as total_searches,
    AVG(results_count) as avg_results,
    AVG(response_time_ms) as avg_response_time,
    COUNT(CASE WHEN no_results THEN 1 END) as no_result_searches,
    COUNT(CASE WHEN user_satisfied THEN 1 END) as satisfied_searches
FROM search_queries
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY search_type, DATE_TRUNC('day', created_at)
ORDER BY search_date DESC, search_type;

COMMENT ON VIEW ml_classification_summary IS 'Summary of ML classification performance over the last 30 days';
COMMENT ON VIEW search_analytics_summary IS 'Daily search analytics summary for the last 30 days';