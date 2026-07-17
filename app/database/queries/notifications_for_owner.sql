SELECT note_access_requests.*, note_access_grants.note_id,
       topics.title AS topic_title,
       COALESCE(users.display_name, 'Deleted administrator') AS admin_name,
       users.email AS admin_email
FROM note_access_requests
JOIN topics ON topics.id = note_access_requests.topic_id
LEFT JOIN note_access_grants
  ON note_access_grants.request_id = note_access_requests.id
LEFT JOIN users ON users.id = note_access_requests.requester_admin_id
WHERE topics.owner_id = %(owner_id)s
ORDER BY note_access_requests.requested_at DESC
