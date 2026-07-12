SELECT labs.id, labs.name, platforms.name AS platform, labs.url,
       labs.visibility, labs.is_deleted, labs.created_at,
       users.id AS owner_id, users.display_name AS owner_name
FROM lab_references AS labs
JOIN lab_platforms AS platforms ON platforms.id = labs.platform_id
JOIN users ON users.id = labs.owner_id
WHERE labs.visibility = 'public'
ORDER BY labs.id
