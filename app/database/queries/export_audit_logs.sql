SELECT audit_logs.id, audit_logs.action, audit_logs.details,
       audit_logs.user_id, users.display_name AS user_name,
       audit_logs.created_at
FROM audit_logs
LEFT JOIN users ON users.id = audit_logs.user_id
ORDER BY audit_logs.id
