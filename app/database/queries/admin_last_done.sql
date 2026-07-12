SELECT audit_logs.action AS title, audit_logs.details AS detail,
       'Completed' AS badge, audit_logs.created_at AS done_at,
       users.display_name AS user_name
FROM audit_logs
LEFT JOIN users ON users.id = audit_logs.user_id
WHERE users.role = 'admin'
   OR audit_logs.action IN (
        'note_access_approved', 'note_access_denied', 'lab_created',
        'lab_updated', 'user_banned', 'user_unbanned', 'admin_backup_exported'
   )
ORDER BY audit_logs.created_at DESC
LIMIT 3
