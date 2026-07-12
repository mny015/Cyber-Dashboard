SELECT note_access_requests.*
FROM note_access_requests
JOIN topics ON topics.id = note_access_requests.topic_id
WHERE note_access_requests.id = %(request_id)s
  AND topics.owner_id = %(owner_id)s
  AND note_access_requests.status = 'pending'
