-- Per-session token usage summary
-- Shows the final (max) capture for each session
SELECT
    session_id,
    model_display_name,
    MAX(total_input_tokens) as final_input_tokens,
    MAX(total_output_tokens) as final_output_tokens,
    MAX(total_cost_usd) as final_cost,
    MAX(used_percentage) as peak_context_pct,
    COUNT(*) as capture_count,
    MIN(capture_timestamp) as first_capture,
    MAX(capture_timestamp) as last_capture
FROM statusbar_captures
GROUP BY session_id, model_display_name
ORDER BY final_cost DESC;
