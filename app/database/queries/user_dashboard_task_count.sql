SELECT COUNT(*) AS total
FROM scheduled_tasks
WHERE status = 'upcoming'
  AND (user_id = %(user_id)s OR scope IN ('admin', 'global'))
