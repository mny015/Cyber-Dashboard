SELECT *
FROM (
    SELECT labs.name AS title, platforms.name AS detail, 'Completed' AS badge,
           completions.completed_at AS done_at
    FROM lab_completions AS completions
    JOIN lab_references AS labs ON labs.id = completions.lab_id
    JOIN lab_platforms AS platforms ON platforms.id = labs.platform_id
    WHERE completions.user_id = %(user_id)s AND labs.is_deleted = 0
    UNION ALL
    SELECT REPLACE(action, '_', ' '), details, 'Completed', created_at
    FROM audit_logs WHERE user_id = %(user_id)s
    UNION ALL
    SELECT title, COALESCE(description, 'Scheduled task completed'), 'Completed', updated_at
    FROM scheduled_tasks WHERE user_id = %(user_id)s AND status = 'completed'
) AS completed_items
ORDER BY done_at DESC
LIMIT 3
