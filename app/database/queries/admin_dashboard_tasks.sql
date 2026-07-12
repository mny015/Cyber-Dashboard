SELECT scheduled_tasks.*,
       COALESCE(creators.display_name, 'Deleted user') AS creator_name
FROM scheduled_tasks
LEFT JOIN users AS creators ON creators.id = scheduled_tasks.created_by
WHERE scheduled_tasks.status = 'upcoming'
  AND scheduled_tasks.scope IN ('admin', 'global')
ORDER BY scheduled_tasks.due_at IS NULL ASC,
         scheduled_tasks.due_at ASC,
         scheduled_tasks.updated_at DESC
LIMIT 4
