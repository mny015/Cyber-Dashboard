SELECT COUNT(*) AS total_notes, MAX(updated_at) AS last_updated
FROM notes
WHERE owner_id = %(owner_id)s
  AND is_deleted = 0
