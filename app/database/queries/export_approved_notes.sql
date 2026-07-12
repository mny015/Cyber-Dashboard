SELECT notes.id, notes.title, notes.body, notes.topic_id,
       notes.owner_id, notes.is_deleted, notes.created_at, notes.updated_at
FROM notes
JOIN note_access_requests AS requests
  ON requests.topic_id = notes.topic_id
 AND requests.note_id = notes.id
WHERE requests.requester_admin_id = %(admin_id)s
  AND requests.status = 'approved'
ORDER BY notes.id
