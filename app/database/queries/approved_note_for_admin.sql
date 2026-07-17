SELECT note_access_requests.id AS request_id,
       notes.title, notes.body, notes.updated_at,
       topics.title AS topic_title,
       owners.display_name AS owner_name, owners.email AS owner_email
FROM note_access_requests
JOIN note_access_grants
  ON note_access_grants.request_id = note_access_requests.id
JOIN notes ON notes.id = note_access_grants.note_id
JOIN topics ON topics.id = note_access_requests.topic_id
JOIN users AS owners ON owners.id = topics.owner_id
WHERE note_access_requests.id = %(request_id)s
  AND note_access_requests.requester_admin_id = %(admin_id)s
  AND note_access_requests.status = 'approved'
  AND notes.is_deleted = 0
