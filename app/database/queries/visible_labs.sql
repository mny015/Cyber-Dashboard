SELECT labs.*, platforms.name AS platform_name, topics.title AS topic_title,
       owners.display_name AS owner_name, owners.role AS owner_role,
       CASE WHEN completions.id IS NULL THEN 0 ELSE 1 END AS is_completed
FROM lab_references AS labs
JOIN lab_platforms AS platforms ON platforms.id = labs.platform_id
JOIN users AS owners ON owners.id = labs.owner_id
LEFT JOIN topics ON topics.id = labs.topic_id
LEFT JOIN lab_completions AS completions
  ON completions.lab_id = labs.id
 AND completions.user_id = %(user_id)s
WHERE labs.is_deleted = 0
  AND (
        labs.owner_id = %(user_id)s
        OR (labs.visibility = 'public' AND owners.role = 'admin')
  )
  AND (%(platform_id)s IS NULL OR labs.platform_id = %(platform_id)s)
ORDER BY is_completed ASC, labs.updated_at DESC
