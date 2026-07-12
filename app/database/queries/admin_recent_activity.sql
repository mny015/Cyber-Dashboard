SELECT audit_logs.action, audit_logs.details, audit_logs.created_at,
       users.display_name AS user_name
FROM audit_logs
LEFT JOIN users ON users.id = audit_logs.user_id
ORDER BY audit_logs.created_at DESC
LIMIT 5
