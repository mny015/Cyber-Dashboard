SELECT notes.*, topics.title AS topic_title
FROM notes
LEFT JOIN topics ON topics.id = notes.topic_id
WHERE notes.id = %(note_id)s
  AND notes.owner_id = %(owner_id)s
  AND notes.is_deleted = 0
