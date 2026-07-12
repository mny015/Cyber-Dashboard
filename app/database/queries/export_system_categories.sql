SELECT categories.id, categories.name, categories.color,
       categories.is_deleted, categories.created_at,
       users.id AS owner_id, users.display_name AS owner_name
FROM categories
JOIN users ON users.id = categories.owner_id
ORDER BY categories.id
