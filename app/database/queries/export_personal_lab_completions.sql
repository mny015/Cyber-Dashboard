SELECT completions.id, completions.lab_id, labs.name AS lab_name,
       completions.completed_at
FROM lab_completions AS completions
JOIN lab_references AS labs ON labs.id = completions.lab_id
WHERE completions.user_id = %(user_id)s
ORDER BY completions.id
