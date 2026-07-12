SELECT topics.id, topics.title, COUNT(notes.id) AS note_count
FROM topics
LEFT JOIN notes
  ON notes.topic_id = topics.id
 AND notes.owner_id = %(owner_id)s
 AND notes.is_deleted = 0
WHERE topics.owner_id = %(owner_id)s
  AND topics.is_deleted = 0
GROUP BY topics.id, topics.title
ORDER BY topics.title ASC
