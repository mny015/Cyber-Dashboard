SELECT notes.*, topics.title AS topic_title
FROM notes
LEFT JOIN topics ON topics.id = notes.topic_id
WHERE notes.owner_id = %(owner_id)s
  AND notes.is_deleted = 0
  AND (%(topic_id)s IS NULL OR notes.topic_id = %(topic_id)s)
  AND (
        %(search)s = ''
        OR notes.title LIKE %(search_pattern)s
        OR notes.body LIKE %(search_pattern)s
  )
ORDER BY notes.updated_at DESC
