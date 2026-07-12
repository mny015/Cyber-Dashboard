SELECT DATE(activity.event_at) AS activity_day, COUNT(*) AS total
FROM (
    SELECT updated_at AS event_at FROM notes
    WHERE owner_id = %(user_id)s AND is_deleted = 0 AND updated_at >= DATE_SUB(NOW(), INTERVAL 6 DAY)
    UNION ALL
    SELECT updated_at FROM topics
    WHERE owner_id = %(user_id)s AND is_deleted = 0 AND updated_at >= DATE_SUB(NOW(), INTERVAL 6 DAY)
    UNION ALL
    SELECT updated_at FROM categories
    WHERE owner_id = %(user_id)s AND is_deleted = 0 AND updated_at >= DATE_SUB(NOW(), INTERVAL 6 DAY)
    UNION ALL
    SELECT completed_at FROM lab_completions
    WHERE user_id = %(user_id)s AND completed_at >= DATE_SUB(NOW(), INTERVAL 6 DAY)
    UNION ALL
    SELECT updated_at FROM security_findings
    WHERE owner_id = %(user_id)s AND is_deleted = 0 AND updated_at >= DATE_SUB(NOW(), INTERVAL 6 DAY)
    UNION ALL
    SELECT updated_at FROM scheduled_tasks
    WHERE user_id = %(user_id)s AND updated_at >= DATE_SUB(NOW(), INTERVAL 6 DAY)
) AS activity
GROUP BY DATE(activity.event_at)
ORDER BY activity_day
