"""Shared catalog seed values and validated security-choice constants."""

APP_VULNERABILITIES = (
    ("A01:2025", "Broken Access Control", "Web Application", "critical", "OWASP Top 10:2025"),
    ("A02:2025", "Security Misconfiguration", "Web Application", "high", "OWASP Top 10:2025"),
    ("A03:2025", "Software Supply Chain Failures", "Web Application", "critical", "OWASP Top 10:2025"),
    ("A04:2025", "Cryptographic Failures", "Web Application", "high", "OWASP Top 10:2025"),
    ("A05:2025", "Injection", "Web Application", "critical", "OWASP Top 10:2025"),
    ("A06:2025", "Insecure Design", "Web Application", "high", "OWASP Top 10:2025"),
    ("A07:2025", "Authentication Failures", "Web Application", "high", "OWASP Top 10:2025"),
    ("A08:2025", "Software or Data Integrity Failures", "Web Application", "high", "OWASP Top 10:2025"),
    ("A09:2025", "Security Logging and Alerting Failures", "Web Application", "medium", "OWASP Top 10:2025"),
    ("A10:2025", "Mishandling of Exceptional Conditions", "Web Application", "medium", "OWASP Top 10:2025"),
    ("API1:2023", "Broken Object Level Authorization", "API Security", "critical", "OWASP API Security Top 10:2023"),
    ("API2:2023", "Broken Authentication", "API Security", "critical", "OWASP API Security Top 10:2023"),
    ("API3:2023", "Broken Object Property Level Authorization", "API Security", "high", "OWASP API Security Top 10:2023"),
    ("API4:2023", "Unrestricted Resource Consumption", "API Security", "high", "OWASP API Security Top 10:2023"),
    ("API5:2023", "Broken Function Level Authorization", "API Security", "high", "OWASP API Security Top 10:2023"),
    ("API6:2023", "Unrestricted Access to Sensitive Business Flows", "API Security", "medium", "OWASP API Security Top 10:2023"),
    ("API7:2023", "Server Side Request Forgery", "API Security", "high", "OWASP API Security Top 10:2023"),
    ("API8:2023", "Security Misconfiguration", "API Security", "high", "OWASP API Security Top 10:2023"),
    ("API9:2023", "Improper Inventory Management", "API Security", "medium", "OWASP API Security Top 10:2023"),
    ("API10:2023", "Unsafe Consumption of APIs", "API Security", "medium", "OWASP API Security Top 10:2023"),
    ("VAPT-XSS", "Cross-Site Scripting", "Common VAPT", "high", "Common web security testing category"),
    ("VAPT-CSRF", "Cross-Site Request Forgery", "Common VAPT", "medium", "Common web security testing category"),
    ("VAPT-PATH", "Path Traversal", "Common VAPT", "high", "Common web security testing category"),
    ("VAPT-FILE", "Unrestricted File Upload", "Common VAPT", "high", "Common web security testing category"),
    ("VAPT-DESER", "Insecure Deserialization", "Common VAPT", "critical", "Common web security testing category"),
)

THREAT_TACTICS = (
    ("TA0043", "Reconnaissance", "medium"),
    ("TA0042", "Resource Development", "medium"),
    ("TA0001", "Initial Access", "critical"),
    ("TA0002", "Execution", "high"),
    ("TA0003", "Persistence", "high"),
    ("TA0004", "Privilege Escalation", "critical"),
    ("TA0005", "Stealth", "high"),
    ("TA0112", "Defense Impairment", "critical"),
    ("TA0006", "Credential Access", "critical"),
    ("TA0007", "Discovery", "medium"),
    ("TA0008", "Lateral Movement", "critical"),
    ("TA0009", "Collection", "high"),
    ("TA0011", "Command and Control", "critical"),
    ("TA0010", "Exfiltration", "critical"),
    ("TA0040", "Impact", "critical"),
)

SEVERITY_CHOICES = ("info", "low", "medium", "high", "critical")
FINDING_STATUS_CHOICES = ("open", "testing", "managed", "resolved")
ACTIVITY_TYPE_CHOICES = (
    "vulnerability_found",
    "vulnerability_tested",
    "threat_managed",
)
