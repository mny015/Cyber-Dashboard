SELECT topics.*, categories.name AS category_name
FROM topics
LEFT JOIN categories ON categories.id = topics.category_id
WHERE topics.owner_id = %(owner_id)s
  AND topics.is_deleted = 0
  AND (%(category_id)s IS NULL OR topics.category_id = %(category_id)s)
ORDER BY topics.updated_at DESC
