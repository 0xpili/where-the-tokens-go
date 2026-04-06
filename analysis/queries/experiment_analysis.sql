-- Compare control vs treatment for each experiment
SELECT
    e.experiment_id,
    e.experiment_name,
    e.condition,
    e.total_input_tokens,
    e.total_output_tokens,
    e.total_cache_creation,
    e.total_cache_read,
    e.turns_to_completion,
    e.compaction_events,
    e.model,
    e.notes
FROM experiments e
ORDER BY e.experiment_id, e.condition;

-- Token savings per experiment
SELECT
    c.experiment_id,
    c.experiment_name,
    c.total_input_tokens as control_input,
    t.total_input_tokens as treatment_input,
    c.total_input_tokens - t.total_input_tokens as input_saved,
    ROUND(100.0 * (c.total_input_tokens - t.total_input_tokens) / c.total_input_tokens, 1) as pct_saved
FROM experiments c
JOIN experiments t ON c.experiment_id = t.experiment_id
WHERE c.condition = 'control' AND t.condition = 'treatment';
