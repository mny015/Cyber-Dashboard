SELECT topics.id, topics.title, topics.status, topics.priority,
       topics.is_deleted, topics.category_id, topics.created_at,
       topics.updated_at, users.id AS owner_id,
       users.display_name AS owner_name
FROM topics
JOIN users ON users.id = topics.owner_id
ORDER BY topics.id
