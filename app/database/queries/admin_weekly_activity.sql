SELECT DATE(activity.event_at) AS activity_day, COUNT(*) AS total
FROM (
    SELECT created_at AS event_at FROM users
    WHERE created_at >= DATE_SUB(NOW(), INTERVAL 6 DAY)
    UNION ALL
    SELECT created_at FROM topics
    WHERE is_deleted = 0 AND created_at >= DATE_SUB(NOW(), INTERVAL 6 DAY)
    UNION ALL
    SELECT created_at FROM notes
    WHERE is_deleted = 0 AND created_at >= DATE_SUB(NOW(), INTERVAL 6 DAY)
    UNION ALL
    SELECT created_at FROM categories
    WHERE is_deleted = 0 AND created_at >= DATE_SUB(NOW(), INTERVAL 6 DAY)
    UNION ALL
    SELECT updated_at FROM lab_references
    WHERE is_deleted = 0 AND updated_at >= DATE_SUB(NOW(), INTERVAL 6 DAY)
    UNION ALL
    SELECT COALESCE(responded_at, requested_at) FROM note_access_requests
    WHERE COALESCE(responded_at, requested_at) >= DATE_SUB(NOW(), INTERVAL 6 DAY)
    UNION ALL
    SELECT audit_logs.created_at FROM audit_logs
    JOIN users ON users.id = audit_logs.user_id
    WHERE users.role = 'admin' AND audit_logs.created_at >= DATE_SUB(NOW(), INTERVAL 6 DAY)
    UNION ALL
    SELECT updated_at FROM scheduled_tasks
    WHERE scope IN ('admin', 'global') AND updated_at >= DATE_SUB(NOW(), INTERVAL 6 DAY)
) AS activity
GROUP BY DATE(activity.event_at)
ORDER BY activity_day
