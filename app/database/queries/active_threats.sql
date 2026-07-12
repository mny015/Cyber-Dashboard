SELECT *
FROM threat_catalog
WHERE is_active = 1
ORDER BY default_level = 'critical' DESC, name ASC
