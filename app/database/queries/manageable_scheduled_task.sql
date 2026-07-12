SELECT scheduled_tasks.*,
       CASE
           WHEN %(is_admin)s = 1
                AND (created_by = %(user_id)s OR scope IN ('admin', 'global'))
               THEN 1
           WHEN %(is_admin)s = 0
                AND user_id = %(user_id)s
                AND scope = 'personal'
               THEN 1
           ELSE 0
       END AS can_manage
FROM scheduled_tasks
WHERE id = %(task_id)s
