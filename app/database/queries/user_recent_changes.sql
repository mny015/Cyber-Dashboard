SELECT *
FROM (
    SELECT 'Topic' AS item_type, title, status AS detail, updated_at AS changed_at
    FROM topics WHERE owner_id = %(user_id)s AND is_deleted = 0
    UNION ALL
    SELECT 'Note', title, 'Updated', updated_at
    FROM notes WHERE owner_id = %(user_id)s AND is_deleted = 0
    UNION ALL
    SELECT 'Category', name, 'Updated', updated_at
    FROM categories WHERE owner_id = %(user_id)s AND is_deleted = 0
    UNION ALL
    SELECT 'Room completed', labs.name, platforms.name, completions.completed_at
    FROM lab_completions AS completions
    JOIN lab_references AS labs ON labs.id = completions.lab_id
    JOIN lab_platforms AS platforms ON platforms.id = labs.platform_id
    WHERE completions.user_id = %(user_id)s AND labs.is_deleted = 0
    UNION ALL
    SELECT 'Finding', title, status, updated_at
    FROM security_findings WHERE owner_id = %(user_id)s AND is_deleted = 0
    UNION ALL
    SELECT 'Task', title, status, updated_at
    FROM scheduled_tasks WHERE user_id = %(user_id)s
) AS changes
ORDER BY changed_at DESC
LIMIT 6
