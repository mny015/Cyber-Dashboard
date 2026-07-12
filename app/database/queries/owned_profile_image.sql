SELECT images.*
FROM users
JOIN profile_images AS images ON images.image_hash = users.profile_image
WHERE users.id = %(user_id)s
  AND users.profile_image = %(image_hash)s
