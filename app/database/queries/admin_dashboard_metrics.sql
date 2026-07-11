SELECT
    (SELECT COUNT(*) FROM users) AS total_users,
    (SELECT COUNT(*) FROM users WHERE is_banned = 0) AS active_users,
    (SELECT COUNT(*) FROM users WHERE is_banned = 1) AS banned_users,
    (SELECT COUNT(*) FROM users WHERE role = 'admin') AS admin_users,
    (SELECT COUNT(*) FROM topics WHERE is_deleted = 0) AS total_topics,
    (SELECT COUNT(*) FROM notes WHERE is_deleted = 0) AS total_notes,
    (SELECT COUNT(*) FROM categories WHERE is_deleted = 0) AS total_categories,
    (SELECT COUNT(*) FROM lab_references WHERE is_deleted = 0) AS total_labs,
    (SELECT COUNT(*) FROM lab_references
     WHERE is_deleted = 0 AND visibility = 'public') AS shared_labs,
    (SELECT COUNT(*) FROM note_access_requests
     WHERE status = 'pending') AS pending_requests,
    (SELECT COUNT(*) FROM audit_logs
     WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)) AS audit_events_week,
    (SELECT COUNT(*) FROM audit_logs
     WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
       AND (action LIKE %(backup_pattern)s OR action LIKE %(export_pattern)s)) AS backup_exports_week
