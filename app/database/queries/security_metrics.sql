SELECT COUNT(*) AS total,
       SUM(activity_type = 'vulnerability_found') AS found_count,
       SUM(activity_type = 'vulnerability_tested') AS tested_count,
       SUM(activity_type = 'threat_managed') AS managed_count,
       SUM(severity = 'critical') AS critical_count,
       SUM(status IN ('managed', 'resolved')) AS closed_count
FROM security_findings
WHERE owner_id = %(owner_id)s
  AND is_deleted = 0
