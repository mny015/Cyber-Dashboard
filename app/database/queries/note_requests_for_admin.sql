SELECT note_access_requests.*, note_access_grants.note_id,
       topics.title AS topic_title,
       owners.display_name AS owner_name, owners.email AS owner_email,
       notes.title AS note_title
FROM note_access_requests
JOIN topics ON topics.id = note_access_requests.topic_id
JOIN users AS owners ON owners.id = topics.owner_id
LEFT JOIN note_access_grants
  ON note_access_grants.request_id = note_access_requests.id
LEFT JOIN notes ON notes.id = note_access_grants.note_id
WHERE note_access_requests.requester_admin_id = %(admin_id)s
ORDER BY note_access_requests.requested_at DESC
