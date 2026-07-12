SELECT scheduled_tasks.*,
       COALESCE(creators.display_name, 'Deleted user') AS creator_name,
       assignees.display_name AS assignee_name
FROM scheduled_tasks
LEFT JOIN users AS creators ON creators.id = scheduled_tasks.created_by
LEFT JOIN users AS assignees ON assignees.id = scheduled_tasks.user_id
WHERE (%(status)s IS NULL OR scheduled_tasks.status = %(status)s)
  AND (
        (
            %(is_admin)s = 1
            AND (
                   scheduled_tasks.created_by = %(user_id)s
                OR scheduled_tasks.scope IN ('admin', 'global')
                OR scheduled_tasks.user_id = %(user_id)s
            )
        )
        OR
        (
            %(is_admin)s = 0
            AND (
                   scheduled_tasks.user_id = %(user_id)s
                OR (
                    scheduled_tasks.scope IN ('admin', 'global')
                    AND scheduled_tasks.status = 'upcoming'
                )
            )
        )
  )
ORDER BY scheduled_tasks.status = 'upcoming' DESC,
         scheduled_tasks.due_at IS NULL ASC,
         scheduled_tasks.due_at ASC,
         scheduled_tasks.updated_at DESC
