SELECT labs.name, platforms.name AS platform_name,
       owners.display_name AS owner_name,
       COUNT(completions.id) AS completion_count, labs.updated_at
FROM lab_references AS labs
JOIN lab_platforms AS platforms ON platforms.id = labs.platform_id
JOIN users AS owners ON owners.id = labs.owner_id
LEFT JOIN lab_completions AS completions ON completions.lab_id = labs.id
WHERE labs.is_deleted = 0 AND labs.visibility = 'public'
GROUP BY labs.id, labs.name, platforms.name, owners.display_name, labs.updated_at
ORDER BY labs.updated_at DESC
LIMIT 5
