SELECT categories.id, categories.name, categories.color, categories.updated_at,
       users.display_name AS owner_name,
       users.email AS owner_email,
       COUNT(topics.id) AS topic_count
FROM categories
JOIN users ON users.id = categories.owner_id
LEFT JOIN topics
  ON topics.category_id = categories.id
 AND topics.is_deleted = 0
WHERE categories.is_deleted = 0
GROUP BY categories.id, categories.name, categories.color, categories.updated_at,
         users.display_name, users.email
ORDER BY categories.updated_at DESC
