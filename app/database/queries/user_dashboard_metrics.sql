SELECT
    (SELECT COUNT(*)
     FROM topics
     WHERE owner_id = %(user_id)s AND is_deleted = 0) AS topics,
    (SELECT COUNT(*)
     FROM notes
     WHERE owner_id = %(user_id)s AND is_deleted = 0) AS notes,
    (SELECT COUNT(*)
     FROM notes
     WHERE owner_id = %(user_id)s AND is_deleted = 0
       AND updated_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)) AS notes_this_week,
    (SELECT COUNT(*)
     FROM categories AS categories
     JOIN users AS owners ON owners.id = categories.owner_id
     WHERE categories.is_deleted = 0
       AND (categories.owner_id = %(user_id)s OR owners.role = 'admin')) AS categories,
    (SELECT COUNT(*)
     FROM note_access_requests AS requests
     JOIN topics ON topics.id = requests.topic_id
     WHERE topics.owner_id = %(user_id)s AND requests.status = 'pending') AS pending_requests,
    (SELECT COUNT(*)
     FROM security_findings
     WHERE owner_id = %(user_id)s AND is_deleted = 0) AS security_findings
