-- Token Research DuckDB Schema
-- Per D-12: DuckDB used for cross-session statistical analysis and querying

-- Statusbar captures: per-turn token data from live sessions
CREATE TABLE IF NOT EXISTS statusbar_captures (
    capture_id VARCHAR DEFAULT gen_random_uuid()::VARCHAR,
    session_id VARCHAR NOT NULL,
    capture_timestamp TIMESTAMP,
    model_id VARCHAR,
    model_display_name VARCHAR,
    claude_code_version VARCHAR,
    total_cost_usd DOUBLE,
    total_duration_ms BIGINT,
    total_input_tokens BIGINT,
    total_output_tokens BIGINT,
    context_window_size INTEGER,
    used_percentage DOUBLE,
    current_input_tokens BIGINT,
    current_output_tokens BIGINT,
    cache_creation_input_tokens BIGINT,
    cache_read_input_tokens BIGINT,
    five_hour_used_pct DOUBLE,
    transcript_path VARCHAR
);

-- Baseline component measurements: per-component overhead from count_tokens API
CREATE TABLE IF NOT EXISTS baseline_components (
    measurement_id VARCHAR DEFAULT gen_random_uuid()::VARCHAR,
    measurement_date TIMESTAMP DEFAULT current_timestamp,
    component VARCHAR NOT NULL,
    tokens_mean DOUBLE,
    tokens_min INTEGER,
    tokens_max INTEGER,
    tokens_stdev DOUBLE,
    model VARCHAR,
    claude_code_version VARCHAR,
    repeat_count INTEGER,
    notes VARCHAR
);

-- Experiment results: before/after comparisons
CREATE TABLE IF NOT EXISTS experiments (
    experiment_id VARCHAR NOT NULL,
    experiment_name VARCHAR,
    experiment_date TIMESTAMP,
    hypothesis VARCHAR,
    condition VARCHAR NOT NULL,  -- 'control' or 'treatment'
    session_id VARCHAR,
    total_input_tokens BIGINT,
    total_output_tokens BIGINT,
    total_cache_creation BIGINT,
    total_cache_read BIGINT,
    session_duration_ms BIGINT,
    turns_to_completion INTEGER,
    compaction_events INTEGER,
    model VARCHAR,
    claude_code_version VARCHAR,
    mcp_servers VARCHAR,
    claude_md_hash VARCHAR,
    notes VARCHAR
);

-- Tool cost measurements
CREATE TABLE IF NOT EXISTS tool_costs (
    measurement_id VARCHAR DEFAULT gen_random_uuid()::VARCHAR,
    measurement_date TIMESTAMP DEFAULT current_timestamp,
    tool_name VARCHAR NOT NULL,
    schema_tokens INTEGER,
    model VARCHAR,
    repeat_count INTEGER,
    measurements VARCHAR  -- JSON array of individual measurements
);
