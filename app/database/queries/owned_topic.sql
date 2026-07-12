SELECT topics.*, categories.name AS category_name
FROM topics
LEFT JOIN categories ON categories.id = topics.category_id
WHERE topics.id = %(topic_id)s
  AND topics.owner_id = %(owner_id)s
  AND topics.is_deleted = 0
