SELECT requests.id, requests.topic_id, grants.note_id,
       COALESCE(admins.display_name, 'Deleted administrator') AS requested_by,
       requests.status, requests.requested_at, requests.responded_at
FROM note_access_requests AS requests
JOIN topics ON topics.id = requests.topic_id
LEFT JOIN note_access_grants AS grants ON grants.request_id = requests.id
LEFT JOIN users AS admins ON admins.id = requests.requester_admin_id
WHERE topics.owner_id = %(user_id)s
ORDER BY requests.id
