-- Compare baseline component measurements across dates/models
SELECT
    component,
    model,
    tokens_mean,
    tokens_min,
    tokens_max,
    tokens_stdev,
    measurement_date,
    notes
FROM baseline_components
ORDER BY tokens_mean DESC;
