SELECT audit_logs.*, users.email AS user_email
FROM audit_logs
LEFT JOIN users ON users.id = audit_logs.user_id
ORDER BY audit_logs.created_at DESC
LIMIT %(limit)s OFFSET %(offset)s
