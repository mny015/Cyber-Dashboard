SELECT platforms.name,
       COUNT(DISTINCT labs.id) AS total_labs,
       COUNT(DISTINCT CASE WHEN labs.visibility = 'public' THEN labs.id END) AS shared_labs,
       COUNT(completions.id) AS completions
FROM lab_platforms AS platforms
LEFT JOIN lab_references AS labs
  ON labs.platform_id = platforms.id AND labs.is_deleted = 0
LEFT JOIN lab_completions AS completions ON completions.lab_id = labs.id
GROUP BY platforms.id, platforms.name
ORDER BY total_labs DESC, platforms.name ASC
LIMIT 5
