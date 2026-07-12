SELECT labs.id, labs.name AS title, platforms.name AS detail,
       owners.display_name AS owner_name, labs.visibility, labs.updated_at
FROM lab_references AS labs
JOIN lab_platforms AS platforms ON platforms.id = labs.platform_id
JOIN users AS owners ON owners.id = labs.owner_id
LEFT JOIN lab_completions AS completions
  ON completions.lab_id = labs.id AND completions.user_id = %(user_id)s
WHERE labs.is_deleted = 0
  AND completions.id IS NULL
  AND (labs.owner_id = %(user_id)s OR (labs.visibility = 'public' AND owners.role = 'admin'))
ORDER BY labs.updated_at DESC
LIMIT 3
