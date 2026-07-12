SELECT labs.id, labs.name, platforms.name AS platform, labs.url,
       labs.notes, labs.topic_id, labs.visibility, labs.is_deleted,
       labs.created_at, labs.updated_at
FROM lab_references AS labs
JOIN lab_platforms AS platforms ON platforms.id = labs.platform_id
WHERE labs.owner_id = %(user_id)s
ORDER BY labs.id
