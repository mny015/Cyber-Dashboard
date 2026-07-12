SELECT requests.id, topics.title AS topic_title,
       owners.display_name AS owner_name, requests.requested_at
FROM note_access_requests AS requests
JOIN topics ON topics.id = requests.topic_id
JOIN users AS owners ON owners.id = topics.owner_id
WHERE requests.status = 'pending'
ORDER BY requests.requested_at DESC
LIMIT 3
