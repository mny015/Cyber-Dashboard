SELECT findings.*, vulns.name AS vulnerability_name,
       vulns.code AS vulnerability_code,
       threats.name AS threat_name,
       threats.code AS threat_code
FROM security_findings AS findings
LEFT JOIN vulnerability_catalog AS vulns ON vulns.id = findings.vulnerability_id
LEFT JOIN threat_catalog AS threats ON threats.id = findings.threat_id
WHERE findings.owner_id = %(owner_id)s
  AND findings.is_deleted = 0
ORDER BY findings.detected_at DESC, findings.updated_at DESC
