SELECT topics.id, topics.title, topics.status, topics.priority, topics.updated_at,
       categories.name AS category_name,
       users.display_name AS owner_name,
       users.email AS owner_email
FROM topics
JOIN users ON users.id = topics.owner_id
LEFT JOIN categories ON categories.id = topics.category_id
WHERE topics.is_deleted = 0
ORDER BY topics.updated_at DESC
