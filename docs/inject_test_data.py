"""Inject a coherent, realistic demo dataset into a confirmed local database.

Run from the project root:

    python docs/inject_test_data.py --confirm-db cyber_dashboard

Use ``--replace`` to remove a previous copy of this demo dataset before inserting it
again. The script never removes records outside the fixed demo user accounts.
"""

from __future__ import annotations

import argparse
import os
import secrets
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

from email_validator import EmailNotValidError, validate_email

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app  # noqa: E402
from app.utils.database import DatabaseError, db, transaction  # noqa: E402
from app.utils.security import hash_password  # noqa: E402
from app.utils.security_catalog import APP_VULNERABILITIES, THREAT_TACTICS  # noqa: E402
from app.utils.validation import PASSWORD_MAX_LENGTH, PASSWORD_MIN_LENGTH  # noqa: E402
from scripts.seed import seed_database  # noqa: E402

SYSTEM_DATABASES = {"information_schema", "mysql", "performance_schema", "sys"}
SUPPORTED_PLATFORM_SLUGS = {"picoctf", "tryhackme", "hack-the-box", "portswigger"}
DEMO_SUGGESTION_CODE = "DEMO-HEADER-001"
LEGACY_DEMO_EMAILS = (
    "admin.demo@cyberdashboard.test",
    "maya.patel@cyberdashboard.test",
    "jordan.lee@cyberdashboard.test",
    "samira.khan@cyberdashboard.test",
)

DEMO_USERS = (
    {
        "key": "admin",
        "email": "admin.demo@demo.cyberdashboard.dev",
        "display_name": "Avery Morgan",
        "role": "admin",
        "bio": (
            "Cyber Dashboard administrator coordinating shared practice labs, account "
            "reviews, and audit evidence."
        ),
        "categories": (
            {
                "key": "shared-web-security",
                "name": "Shared Web Security",
                "description": (
                    "Curated web security material published for every learner on the "
                    "platform."
                ),
                "color": "#79cda7",
                "topics": (
                    {
                        "key": "shared-web-foundations",
                        "title": "HTTP and Web Request Foundations",
                        "status": "complete",
                        "priority": "high",
                        "description": (
                            "Understand request structure, methods, headers, response codes, "
                            "and safe testing workflows."
                        ),
                        "summary": (
                            "Shared baseline material for learners preparing to test web "
                            "applications."
                        ),
                        "note": {
                            "key": "shared-http-review-note",
                            "title": "HTTP Request Review Workflow",
                            "body": """# HTTP Request Review Workflow

## Review sequence

1. Identify the request method, host, path, and parameters.
2. Record authentication and authorization context.
3. Compare successful and rejected responses.
4. Retest only inside the authorized lab environment.

## Practice

- [HTB Academy: Web Requests](https://academy.hackthebox.com/course/preview/web-requests)
- [picoCTF practice](https://play.picoctf.org/practice)

Keep screenshots and observations, but never store real credentials in notes.
""",
                        },
                        "labs": (
                            {
                                "key": "shared-htb-web-requests",
                                "name": "HTB Academy: Web Requests",
                                "platform": "hack-the-box",
                                "url": (
                                    "https://academy.hackthebox.com/course/preview/web-requests"
                                ),
                                "notes": (
                                    "Fundamental HTTP module covering requests, responses, "
                                    "headers, methods, status codes, cURL, and API interaction."
                                ),
                                "visibility": "public",
                            },
                            {
                                "key": "shared-pico-web-practice",
                                "name": "picoCTF: Web Exploitation Practice",
                                "platform": "picoctf",
                                "url": "https://play.picoctf.org/practice",
                                "notes": (
                                    "Year-round legal challenge practice. Filter the practice "
                                    "area to Web Exploitation and record each solved concept."
                                ),
                                "visibility": "public",
                            },
                        ),
                    },
                    {
                        "key": "shared-owasp-risk-review",
                        "title": "OWASP Risk Review",
                        "status": "learning",
                        "priority": "high",
                        "description": (
                            "Review common web application risks and connect each risk to a "
                            "repeatable lab exercise."
                        ),
                        "summary": (
                            "Shared topic for practical OWASP review and safe verification."
                        ),
                        "note": {
                            "key": "shared-owasp-review-note",
                            "title": "OWASP Practice Review Notes",
                            "body": """# OWASP Practice Review

## What to capture

- The vulnerable trust boundary.
- The observable impact.
- The control that should prevent recurrence.
- A concise retest condition.

## Practice

- [TryHackMe: OWASP Top 10](https://tryhackme.com/room/owasptop10)
- [PortSwigger: SQL injection - retrieving hidden data](https://portswigger.net/web-security/sql-injection/lab-retrieve-hidden-data)

Use only the deliberately vulnerable targets supplied by each platform.
""",
                        },
                        "labs": (
                            {
                                "key": "shared-thm-owasp",
                                "name": "TryHackMe: OWASP Top 10",
                                "platform": "tryhackme",
                                "url": "https://tryhackme.com/room/owasptop10",
                                "notes": (
                                    "Beginner room that explains common OWASP risks and pairs "
                                    "the theory with supporting practical challenges."
                                ),
                                "visibility": "public",
                            },
                            {
                                "key": "shared-portswigger-sqli",
                                "name": "PortSwigger: SQL Injection - Hidden Data",
                                "platform": "portswigger",
                                "url": (
                                    "https://portswigger.net/web-security/sql-injection/"
                                    "lab-retrieve-hidden-data"
                                ),
                                "notes": (
                                    "Apprentice SQL injection lab focused on retrieving hidden "
                                    "records from a deliberately vulnerable product filter."
                                ),
                                "visibility": "public",
                            },
                        ),
                    },
                ),
            },
            {
                "key": "shared-defensive-operations",
                "name": "Shared Defensive Operations",
                "description": (
                    "Platform-wide networking and defensive-security foundations for "
                    "analysts and testers."
                ),
                "color": "#7fc5a4",
                "topics": (
                    {
                        "key": "shared-network-defense",
                        "title": "Network and SOC Foundations",
                        "status": "learning",
                        "priority": "medium",
                        "description": (
                            "Build a shared understanding of network traffic, defensive "
                            "operations, evidence sources, and analyst responsibilities."
                        ),
                        "summary": (
                            "Common networking and defensive-security material available to "
                            "every learner."
                        ),
                        "note": {
                            "key": "shared-network-defense-note",
                            "title": "Network and SOC Foundation Notes",
                            "body": """# Network and SOC Foundations

## Learning goals

- Explain how hosts communicate across private and public networks.
- Identify useful SOC evidence sources and their limitations.
- Connect network observations to a documented investigation timeline.

## Practice

- [TryHackMe: Network Fundamentals](https://tryhackme.com/module/network-fundamentals)
- [TryHackMe: Introduction to Defensive Security](https://tryhackme.com/module/introduction-to-defensive-security)

Record concepts and observations without copying credentials or sensitive lab data.
""",
                        },
                        "labs": (
                            {
                                "key": "shared-thm-network-fundamentals",
                                "name": "TryHackMe: Network Fundamentals",
                                "platform": "tryhackme",
                                "url": "https://tryhackme.com/module/network-fundamentals",
                                "notes": (
                                    "Interactive networking module covering LAN design, the OSI "
                                    "model, packets, frames, and extending a network."
                                ),
                                "visibility": "public",
                            },
                            {
                                "key": "shared-thm-defensive-security",
                                "name": "TryHackMe: Introduction to Defensive Security",
                                "platform": "tryhackme",
                                "url": (
                                    "https://tryhackme.com/module/"
                                    "introduction-to-defensive-security"
                                ),
                                "notes": (
                                    "Defensive-security module introducing SOC responsibilities, "
                                    "digital forensics, evidence, and operational workflows."
                                ),
                                "visibility": "public",
                            },
                        ),
                    },
                ),
            },
        ),
        "contacts": (
            {
                "name": "Training Platform Support",
                "email": "support@demo.cyberdashboard.dev",
                "phone": "+1 202-555-0100",
                "notes": "Synthetic support contact used to demonstrate private contact records.",
            },
        ),
        "findings": (
            {
                "title": "Shared lab link validation review",
                "activity_type": "vulnerability_tested",
                "vulnerability": "A02:2025",
                "threat": None,
                "target": "training-library.cyberdashboard.test",
                "severity": "low",
                "status": "resolved",
                "evidence": (
                    "Validated HTTPS schemes, approved hostnames, and expected redirects for "
                    "all shared lab references."
                ),
                "notes": "No unsafe schemes or unexpected external redirects were observed.",
                "days_ago": 3,
            },
            {
                "title": "Shared resource response headers differ by route",
                "activity_type": "vulnerability_found",
                "vulnerability": "A02:2025",
                "threat": None,
                "target": "training-library.cyberdashboard.test",
                "severity": "medium",
                "status": "open",
                "evidence": (
                    "Synthetic header review found the expected frame and content policies on "
                    "most routes but not on one legacy download response."
                ),
                "notes": "Apply the shared response policy and repeat the route inventory.",
                "days_ago": 1,
            },
        ),
        "tasks": (
            {
                "title": "Review pending note access requests",
                "description": "Check the request scope and avoid requesting unrelated notes.",
                "task_type": "review",
                "days_due": 2,
                "status": "upcoming",
                "scope": "admin",
            },
            {
                "title": "Complete one shared web security lab",
                "description": "Platform-wide practice task using one of the shared labs.",
                "task_type": "lab",
                "days_due": 5,
                "status": "upcoming",
                "scope": "global",
            },
            {
                "title": "Verify weekly backup archive",
                "description": "Confirm the archive opens and contains the expected exports.",
                "task_type": "backup",
                "days_due": -4,
                "status": "completed",
                "scope": "admin",
            },
        ),
        "work_logs": (
            {
                "title": "Shared lab quality review",
                "log_type": "GRC",
                "content": (
                    "Reviewed ownership, visibility, HTTPS links, and descriptive metadata for "
                    "the shared lab library."
                ),
                "evidence_url": "https://example.test/evidence/shared-lab-review",
                "risk_rating": "Low",
                "days_ago": 4,
            },
        ),
        "reflections": (
            {
                "insight": "Shared labs are more useful when each one has a specific learning goal.",
                "challenge": "Keeping descriptions concise while retaining enough context.",
                "next_step": "Review completion trends before adding more advanced material.",
                "days_ago": 2,
            },
        ),
    },
    {
        "key": "maya",
        "email": "maya.patel@demo.cyberdashboard.dev",
        "display_name": "Maya Patel",
        "role": "user",
        "bio": (
            "Application security analyst practicing API authorization, injection testing, "
            "and evidence-based retesting."
        ),
        "categories": (
            {
                "key": "maya-web-assurance",
                "name": "Web Application Assurance",
                "description": (
                    "Structured testing notes for web and API security verification."
                ),
                "color": "#8fd3d8",
                "topics": (
                    {
                        "key": "maya-sqli-verification",
                        "title": "SQL Injection Verification",
                        "status": "practicing",
                        "priority": "high",
                        "description": (
                            "Practice error-based, UNION, and blind SQL injection verification "
                            "inside authorized labs."
                        ),
                        "summary": (
                            "A repeatable checklist for confirming injection behavior and "
                            "documenting remediation."
                        ),
                        "note": {
                            "key": "maya-sqli-note",
                            "title": "SQL Injection Retest Checklist",
                            "body": """# SQL Injection Retest Checklist

## Before testing

- Confirm written authorization and the exact target.
- Capture the baseline response and normal database behavior.
- Use the least invasive proof required.

## Retest criteria

- Input is passed through parameterized queries.
- Error responses do not disclose database details.
- Boolean and time-based probes no longer change behavior.

## Practice

- [PortSwigger blind SQL injection lab](https://portswigger.net/web-security/sql-injection/blind/lab-conditional-responses)
- [HTB Academy SQL Injection Fundamentals](https://academy.hackthebox.com/course/preview/sql-injection-fundamentals/intro-to-databases)
""",
                        },
                        "labs": (
                            {
                                "key": "maya-portswigger-blind-sqli",
                                "name": "PortSwigger: Blind SQLi Conditional Responses",
                                "platform": "portswigger",
                                "url": (
                                    "https://portswigger.net/web-security/sql-injection/blind/"
                                    "lab-conditional-responses"
                                ),
                                "notes": (
                                    "Practice identifying blind SQL injection through "
                                    "conditional response differences."
                                ),
                                "visibility": "personal",
                            },
                            {
                                "key": "maya-htb-sqli",
                                "name": "HTB Academy: SQL Injection Fundamentals",
                                "platform": "hack-the-box",
                                "url": (
                                    "https://academy.hackthebox.com/course/preview/"
                                    "sql-injection-fundamentals/intro-to-databases"
                                ),
                                "notes": (
                                    "MySQL-focused module covering SQL fundamentals, UNION "
                                    "injection, enumeration, and mitigation."
                                ),
                                "visibility": "personal",
                            },
                        ),
                    },
                    {
                        "key": "maya-access-control",
                        "title": "Access Control Testing",
                        "status": "in-progress",
                        "priority": "high",
                        "description": (
                            "Test vertical and horizontal authorization decisions with "
                            "owner-scoped evidence."
                        ),
                        "summary": (
                            "Focus on object ownership, administrative functions, and direct "
                            "request authorization."
                        ),
                        "note": {
                            "key": "maya-access-control-note",
                            "title": "Authorization Test Matrix",
                            "body": """# Authorization Test Matrix

| Actor | Object owner | Expected result |
| --- | --- | --- |
| Anonymous | Any | Redirect or deny |
| User A | User A | Allow intended action |
| User A | User B | Deny with no data disclosure |
| Administrator | Private note | Require explicit owner approval |

## Practice

- [PortSwigger unprotected admin functionality lab](https://portswigger.net/web-security/access-control/lab-unprotected-admin-functionality-with-unpredictable-url)
""",
                        },
                        "labs": (
                            {
                                "key": "maya-portswigger-access-control",
                                "name": "PortSwigger: Unprotected Admin Functionality",
                                "platform": "portswigger",
                                "url": (
                                    "https://portswigger.net/web-security/access-control/"
                                    "lab-unprotected-admin-functionality-with-unpredictable-url"
                                ),
                                "notes": (
                                    "Access-control lab where a hidden administrative path is "
                                    "disclosed by client-side code."
                                ),
                                "visibility": "personal",
                            },
                        ),
                    },
                ),
            },
            {
                "key": "maya-authentication-assurance",
                "name": "Authentication Assurance",
                "description": (
                    "Account recovery, login protection, session, and password workflow "
                    "verification."
                ),
                "color": "#9abfe6",
                "topics": (
                    {
                        "key": "maya-account-recovery",
                        "title": "Account Recovery and Login Controls",
                        "status": "practicing",
                        "priority": "high",
                        "description": (
                            "Review account recovery tokens, password changes, lockout "
                            "behavior, and user-bound authorization."
                        ),
                        "summary": (
                            "Practical checks for preventing account takeover through "
                            "secondary authentication workflows."
                        ),
                        "note": {
                            "key": "maya-account-recovery-note",
                            "title": "Account Recovery Test Plan",
                            "body": """# Account Recovery Test Plan

## Verification points

- Recovery tokens are random, short-lived, single-use, and user-bound.
- Password changes require the current authenticated identity.
- Login controls resist automation without enabling easy account denial of service.
- Successful resets invalidate older sessions when required.

## Practice

- [PortSwigger: Password reset broken logic](https://portswigger.net/web-security/authentication/other-mechanisms/lab-password-reset-broken-logic)
- [PortSwigger: Password brute-force via password change](https://portswigger.net/web-security/authentication/other-mechanisms/lab-password-brute-force-via-password-change)
""",
                        },
                        "labs": (
                            {
                                "key": "maya-portswigger-reset-logic",
                                "name": "PortSwigger: Password Reset Broken Logic",
                                "platform": "portswigger",
                                "url": (
                                    "https://portswigger.net/web-security/authentication/"
                                    "other-mechanisms/lab-password-reset-broken-logic"
                                ),
                                "notes": (
                                    "Authentication lab focused on a reset workflow that fails "
                                    "to bind the submitted account to the recovery authorization."
                                ),
                                "visibility": "personal",
                            },
                            {
                                "key": "maya-portswigger-password-change",
                                "name": "PortSwigger: Password Change Brute-Force",
                                "platform": "portswigger",
                                "url": (
                                    "https://portswigger.net/web-security/authentication/"
                                    "other-mechanisms/"
                                    "lab-password-brute-force-via-password-change"
                                ),
                                "notes": (
                                    "Authentication lab demonstrating why password-change "
                                    "responses and lockout behavior need consistent protection."
                                ),
                                "visibility": "personal",
                            },
                        ),
                    },
                ),
            },
        ),
        "contacts": (
            {
                "name": "Nina Brooks",
                "email": "nina.brooks@demo.cyberdashboard.dev",
                "phone": "+1 202-555-0148",
                "notes": "Synthetic application owner contact for retest coordination.",
            },
        ),
        "findings": (
            {
                "title": "Invoice API object ownership bypass",
                "activity_type": "vulnerability_found",
                "vulnerability": "API1:2023",
                "threat": None,
                "target": "staging-api.northstar-demo.test/v1/invoices/{id}",
                "severity": "high",
                "status": "resolved",
                "evidence": (
                    "A user account could previously retrieve another synthetic tenant's "
                    "invoice by changing the object identifier."
                ),
                "notes": (
                    "Retest confirmed owner filtering is now enforced in the repository query."
                ),
                "days_ago": 8,
            },
            {
                "title": "Search filter blind SQL injection indicator",
                "activity_type": "vulnerability_tested",
                "vulnerability": "A05:2025",
                "threat": None,
                "target": "qa-store.northstar-demo.test/search",
                "severity": "critical",
                "status": "testing",
                "evidence": (
                    "Authorized QA requests showed repeatable conditional response differences "
                    "before the query was converted to parameters."
                ),
                "notes": "Awaiting final retest against the patched QA build.",
                "days_ago": 2,
            },
            {
                "title": "Password reset submission not bound to requested account",
                "activity_type": "vulnerability_tested",
                "vulnerability": "A07:2025",
                "threat": "TA0006",
                "target": "accounts.northstar-demo.test/reset-password",
                "severity": "high",
                "status": "testing",
                "evidence": (
                    "An authorized QA workflow accepted an account identifier from the final "
                    "form instead of deriving it from the recovery token."
                ),
                "notes": (
                    "Bind the token to one account, expire it after use, and invalidate prior "
                    "sessions after the password changes."
                ),
                "days_ago": 1,
            },
        ),
        "tasks": (
            {
                "title": "Retest invoice object authorization",
                "description": "Verify owner scoping across read, update, and export operations.",
                "task_type": "review",
                "days_due": 3,
                "status": "upcoming",
                "scope": "personal",
            },
            {
                "title": "Finish blind SQL injection lab",
                "description": "Complete the conditional response exercise and summarize controls.",
                "task_type": "lab",
                "days_due": -2,
                "status": "completed",
                "scope": "personal",
            },
        ),
        "work_logs": (
            {
                "title": "Invoice API authorization retest",
                "log_type": "VAPT",
                "content": (
                    "Repeated the object-level authorization matrix with two synthetic tenants "
                    "and confirmed denied cross-tenant access."
                ),
                "evidence_url": "https://example.test/evidence/invoice-api-retest",
                "risk_rating": "High",
                "days_ago": 7,
            },
        ),
        "reflections": (
            {
                "insight": (
                    "Ownership checks are strongest when included directly in the data-access "
                    "predicate."
                ),
                "challenge": "Keeping retest evidence useful without storing sensitive payloads.",
                "next_step": "Create the same authorization matrix for export endpoints.",
                "days_ago": 1,
            },
        ),
    },
    {
        "key": "jordan",
        "email": "jordan.lee@demo.cyberdashboard.dev",
        "display_name": "Jordan Lee",
        "role": "user",
        "bio": (
            "SOC analyst building repeatable alert triage, log correlation, and credential "
            "access investigation workflows."
        ),
        "categories": (
            {
                "key": "jordan-detection",
                "name": "Detection Engineering",
                "description": "SIEM investigation notes, alert logic, and response exercises.",
                "color": "#f1c96f",
                "topics": (
                    {
                        "key": "jordan-siem-triage",
                        "title": "SIEM Alert Triage",
                        "status": "learning",
                        "priority": "high",
                        "description": (
                            "Correlate endpoint, authentication, web, and network events before "
                            "assigning an alert outcome."
                        ),
                        "summary": (
                            "A practical workflow for validating true positives and documenting "
                            "analyst decisions."
                        ),
                        "note": {
                            "key": "jordan-siem-note",
                            "title": "SIEM Investigation Worksheet",
                            "body": """# SIEM Investigation Worksheet

## Initial triage

- Identify the rule, data source, user, host, and time range.
- Build a five-minute event timeline around the alert.
- Compare the activity with the user's normal pattern.
- Record containment or tuning actions.

## Practice

- [TryHackMe: Introduction to SIEM](https://tryhackme.com/room/introtosiem)

Classify the result as a true positive, false positive, or unresolved investigation.
""",
                        },
                        "labs": (
                            {
                                "key": "jordan-thm-intro-siem",
                                "name": "TryHackMe: Introduction to SIEM",
                                "platform": "tryhackme",
                                "url": "https://tryhackme.com/room/introtosiem",
                                "notes": (
                                    "Introduction to SIEM log collection, normalization, "
                                    "correlation, alerting, dashboards, and investigation."
                                ),
                                "visibility": "personal",
                            },
                        ),
                    },
                    {
                        "key": "jordan-credential-access",
                        "title": "Credential Access Triage",
                        "status": "practicing",
                        "priority": "high",
                        "description": (
                            "Investigate failed-login bursts, suspicious successful logins, and "
                            "follow-on activity."
                        ),
                        "summary": (
                            "Link authentication evidence to host and network context before "
                            "escalation."
                        ),
                        "note": {
                            "key": "jordan-credential-note",
                            "title": "Credential Alert Decision Notes",
                            "body": """# Credential Alert Decision Notes

## Escalation signals

- Multiple accounts targeted from one source.
- A successful login after repeated failures.
- New geography, device, or impossible travel.
- Follow-on discovery, collection, or outbound traffic.

## Practice

- [HTB Academy: Getting Started](https://academy.hackthebox.com/course/preview/getting-started)

Always preserve timestamps and source identifiers before containment.
""",
                        },
                        "labs": (
                            {
                                "key": "jordan-htb-getting-started",
                                "name": "HTB Academy: Getting Started",
                                "platform": "hack-the-box",
                                "url": (
                                    "https://academy.hackthebox.com/course/preview/getting-started"
                                ),
                                "notes": (
                                    "Guided penetration-testing fundamentals with scanning, "
                                    "enumeration, shells, and a first retired box workflow."
                                ),
                                "visibility": "personal",
                            },
                        ),
                    },
                ),
            },
            {
                "key": "jordan-network-monitoring",
                "name": "Network Monitoring",
                "description": (
                    "Traffic analysis, perimeter telemetry, and network-forensics exercises."
                ),
                "color": "#d9b77e",
                "topics": (
                    {
                        "key": "jordan-perimeter-analysis",
                        "title": "Perimeter Traffic Analysis",
                        "status": "in-progress",
                        "priority": "high",
                        "description": (
                            "Review firewall, flow, and packet evidence to distinguish routine "
                            "traffic from suspicious perimeter activity."
                        ),
                        "summary": (
                            "A repeatable network investigation process from initial alert to "
                            "documented conclusion."
                        ),
                        "note": {
                            "key": "jordan-perimeter-note",
                            "title": "Perimeter Investigation Checklist",
                            "body": """# Perimeter Investigation Checklist

## Evidence sequence

1. Confirm the source, destination, protocol, and time range.
2. Compare firewall actions with flow or packet evidence.
3. Identify repeated scans, beaconing, or unusual outbound volume.
4. Document assumptions before escalating.

## Practice

- [TryHackMe: Network Security Essentials](https://tryhackme.com/room/networksecurityessentials)
- [TryHackMe: NetworkMiner](https://tryhackme.com/room/networkminer)
""",
                        },
                        "labs": (
                            {
                                "key": "jordan-thm-network-security",
                                "name": "TryHackMe: Network Security Essentials",
                                "platform": "tryhackme",
                                "url": (
                                    "https://tryhackme.com/room/networksecurityessentials"
                                ),
                                "notes": (
                                    "Defensive room covering network components, perimeter "
                                    "threats, firewall evidence, and suspicious traffic review."
                                ),
                                "visibility": "personal",
                            },
                            {
                                "key": "jordan-thm-networkminer",
                                "name": "TryHackMe: NetworkMiner",
                                "platform": "tryhackme",
                                "url": "https://tryhackme.com/room/networkminer",
                                "notes": (
                                    "Network-forensics room using NetworkMiner to inspect PCAP "
                                    "sessions, hosts, files, and protocol artifacts."
                                ),
                                "visibility": "personal",
                            },
                        ),
                    },
                ),
            },
        ),
        "contacts": (
            {
                "name": "Ethan Cole",
                "email": "ethan.cole@demo.cyberdashboard.dev",
                "phone": "+1 202-555-0162",
                "notes": "Synthetic incident lead contact used for escalation practice.",
            },
        ),
        "findings": (
            {
                "title": "Password spray followed by successful login",
                "activity_type": "threat_managed",
                "vulnerability": None,
                "threat": "TA0006",
                "target": "vpn-gateway.northstar-demo.test",
                "severity": "critical",
                "status": "managed",
                "evidence": (
                    "Synthetic SIEM timeline correlated 27 failed attempts with one successful "
                    "login and a new device fingerprint."
                ),
                "notes": (
                    "Demo account disabled, synthetic source blocked, and detection threshold "
                    "tuned."
                ),
                "days_ago": 5,
            },
            {
                "title": "Authentication failures missing from alert coverage",
                "activity_type": "vulnerability_found",
                "vulnerability": "A09:2025",
                "threat": "TA0001",
                "target": "identity.northstar-demo.test",
                "severity": "medium",
                "status": "open",
                "evidence": (
                    "Test events reached the log index but no alert mapped repeated failures "
                    "across multiple usernames."
                ),
                "notes": "Create and validate a low-noise password-spray correlation rule.",
                "days_ago": 1,
            },
            {
                "title": "Periodic outbound beacon pattern from test workstation",
                "activity_type": "threat_managed",
                "vulnerability": None,
                "threat": "TA0011",
                "target": "analyst-workstation-07.northstar-demo.test",
                "severity": "high",
                "status": "managed",
                "evidence": (
                    "Synthetic flow records showed a regular 60-second connection interval to "
                    "a designated training endpoint over an uncommon destination port."
                ),
                "notes": (
                    "Isolated the simulated host, preserved the PCAP, and documented the "
                    "expected beacon indicators for future detection tests."
                ),
                "days_ago": 2,
            },
        ),
        "tasks": (
            {
                "title": "Tune failed-login correlation rule",
                "description": "Validate the rule against known-good and synthetic spray traffic.",
                "task_type": "review",
                "days_due": 4,
                "status": "upcoming",
                "scope": "personal",
            },
            {
                "title": "Document SIEM alert triage",
                "description": "Capture the timeline, decision, and response actions.",
                "task_type": "note",
                "days_due": -3,
                "status": "completed",
                "scope": "personal",
            },
        ),
        "work_logs": (
            {
                "title": "Credential access detection review",
                "log_type": "GRC",
                "content": (
                    "Compared current authentication alerts with the documented credential "
                    "access use case and identified a password-spray coverage gap."
                ),
                "evidence_url": "https://example.test/evidence/credential-alert-review",
                "risk_rating": "Medium",
                "days_ago": 3,
            },
        ),
        "reflections": (
            {
                "insight": "One authentication event is weak evidence; a short timeline is stronger.",
                "challenge": "Reducing noise without hiding low-and-slow activity.",
                "next_step": "Test account and source-based aggregation together.",
                "days_ago": 1,
            },
        ),
    },
    {
        "key": "samira",
        "email": "samira.khan@demo.cyberdashboard.dev",
        "display_name": "Samira Khan",
        "role": "user",
        "bio": (
            "Junior penetration tester building strong Linux, HTTP, and reflected XSS "
            "fundamentals through guided labs."
        ),
        "categories": (
            {
                "key": "samira-foundations",
                "name": "Pentest Foundations",
                "description": "Core Linux and web skills required for repeatable lab work.",
                "color": "#a4e6c7",
                "topics": (
                    {
                        "key": "samira-linux-fundamentals",
                        "title": "Linux Command-Line Fundamentals",
                        "status": "in-progress",
                        "priority": "medium",
                        "description": (
                            "Practice navigation, file discovery, permissions, pipes, and safe "
                            "shell habits."
                        ),
                        "summary": "Command-line foundations for lab setup and evidence collection.",
                        "note": {
                            "key": "samira-linux-note",
                            "title": "Linux Lab Command Journal",
                            "body": """# Linux Lab Command Journal

## Commands to practice

- `pwd`, `ls`, `cd`, `file`, and `cat`
- `find`, `grep`, pipes, and redirection
- Reading permissions before changing a file

## Practice

- [TryHackMe: Linux Fundamentals Part 1](https://tryhackme.com/room/linuxfundamentalspart1)

For each command, record what it reads or changes before running it.
""",
                        },
                        "labs": (
                            {
                                "key": "samira-linux-fundamentals-lab",
                                "name": "TryHackMe: Linux Fundamentals Part 1",
                                "platform": "tryhackme",
                                "url": "https://tryhackme.com/room/linuxfundamentalspart1",
                                "notes": (
                                    "Beginner room covering essential Linux commands, filesystem "
                                    "interaction, searching, and shell operators."
                                ),
                                "visibility": "personal",
                            },
                        ),
                    },
                    {
                        "key": "samira-reflected-xss",
                        "title": "Reflected Cross-Site Scripting",
                        "status": "practicing",
                        "priority": "high",
                        "description": (
                            "Understand HTML output contexts, encoding, and safe reflected XSS "
                            "verification."
                        ),
                        "summary": (
                            "Connect browser-observed reflection to the correct contextual "
                            "encoding control."
                        ),
                        "note": {
                            "key": "samira-xss-note",
                            "title": "Reflected XSS Context Notes",
                            "body": """# Reflected XSS Context Notes

## Review

- Identify exactly where input appears in the response.
- Determine whether the context is HTML, attribute, JavaScript, or URL.
- Verify output encoding and the active Content Security Policy.
- Retest only on a deliberately vulnerable lab.

## Practice

- [PortSwigger reflected XSS lab](https://portswigger.net/web-security/cross-site-scripting/reflected/lab-html-context-nothing-encoded)
""",
                        },
                        "labs": (
                            {
                                "key": "samira-portswigger-xss",
                                "name": "PortSwigger: Reflected XSS in HTML Context",
                                "platform": "portswigger",
                                "url": (
                                    "https://portswigger.net/web-security/cross-site-scripting/"
                                    "reflected/lab-html-context-nothing-encoded"
                                ),
                                "notes": (
                                    "Apprentice reflected XSS lab where search input is returned "
                                    "inside an unencoded HTML context."
                                ),
                                "visibility": "personal",
                            },
                        ),
                    },
                ),
            },
            {
                "key": "samira-platform-foundations",
                "name": "Platform Foundations",
                "description": (
                    "Linux administration and networking concepts used throughout practical "
                    "security work."
                ),
                "color": "#8fd0b7",
                "topics": (
                    {
                        "key": "samira-linux-networking",
                        "title": "Linux and Networking Foundations",
                        "status": "learning",
                        "priority": "medium",
                        "description": (
                            "Strengthen command-line administration and networking concepts "
                            "before moving into complex assessment workflows."
                        ),
                        "summary": (
                            "A practical foundation for navigating hosts and interpreting "
                            "network behavior."
                        ),
                        "note": {
                            "key": "samira-linux-network-note",
                            "title": "Linux and Networking Study Notes",
                            "body": """# Linux and Networking Foundations

## Study targets

- Navigate the filesystem and manage permissions deliberately.
- Explain addresses, routes, subnets, DNS, and common transport protocols.
- Record the effect of each command before and after execution.

## Practice

- [HTB Academy: Linux Fundamentals](https://academy.hackthebox.com/course/preview/linux-fundamentals)
- [HTB Academy: Introduction to Networking](https://academy.hackthebox.com/course/preview/introduction-to-networking)
""",
                        },
                        "labs": (
                            {
                                "key": "samira-htb-linux-fundamentals",
                                "name": "HTB Academy: Linux Fundamentals",
                                "platform": "hack-the-box",
                                "url": (
                                    "https://academy.hackthebox.com/course/preview/"
                                    "linux-fundamentals"
                                ),
                                "notes": (
                                    "Fundamental module covering Linux structure, shell usage, "
                                    "files, services, administration, and permissions."
                                ),
                                "visibility": "personal",
                            },
                            {
                                "key": "samira-htb-networking",
                                "name": "HTB Academy: Introduction to Networking",
                                "platform": "hack-the-box",
                                "url": (
                                    "https://academy.hackthebox.com/course/preview/"
                                    "introduction-to-networking"
                                ),
                                "notes": (
                                    "Networking module covering addressing, routing, protocols, "
                                    "and the structures used in assessment environments."
                                ),
                                "visibility": "personal",
                            },
                        ),
                    },
                ),
            },
        ),
        "contacts": (
            {
                "name": "Priya Shah",
                "email": "priya.shah@demo.cyberdashboard.dev",
                "phone": "+1 202-555-0187",
                "notes": "Synthetic mentor contact for weekly lab review.",
            },
        ),
        "findings": (
            {
                "title": "Reflected search input executes in HTML context",
                "activity_type": "vulnerability_tested",
                "vulnerability": "VAPT-XSS",
                "threat": None,
                "target": "qa-helpdesk.northstar-demo.test/search",
                "severity": "high",
                "status": "resolved",
                "evidence": (
                    "Authorized QA response placed the search term into HTML without contextual "
                    "encoding before the template fix."
                ),
                "notes": (
                    "Retest confirmed contextual escaping and a restrictive script policy."
                ),
                "days_ago": 6,
            },
            {
                "title": "Administrative route disclosed in client bundle",
                "activity_type": "vulnerability_found",
                "vulnerability": "A01:2025",
                "threat": "TA0007",
                "target": "preview-console.northstar-demo.test",
                "severity": "high",
                "status": "managed",
                "evidence": (
                    "A source-map reference revealed an administrative path; direct requests "
                    "were rejected after the server-side authorization check."
                ),
                "notes": (
                    "Remove production source maps and retain the server-side role requirement."
                ),
                "days_ago": 2,
            },
            {
                "title": "Development service exposed on lab host",
                "activity_type": "vulnerability_found",
                "vulnerability": "A02:2025",
                "threat": "TA0043",
                "target": "linux-lab-03.northstar-demo.test:8000",
                "severity": "medium",
                "status": "open",
                "evidence": (
                    "A synthetic network inventory found a development service listening on "
                    "all interfaces instead of the intended local interface."
                ),
                "notes": (
                    "Restrict the listener, update the host firewall, and verify the port from "
                    "a separate lab subnet."
                ),
                "days_ago": 1,
            },
        ),
        "tasks": (
            {
                "title": "Complete Linux Fundamentals Part 1",
                "description": "Finish the filesystem search and shell operator exercises.",
                "task_type": "lab",
                "days_due": 3,
                "status": "upcoming",
                "scope": "personal",
            },
            {
                "title": "Summarize reflected XSS mitigations",
                "description": "Document contextual encoding and CSP as separate controls.",
                "task_type": "note",
                "days_due": -1,
                "status": "completed",
                "scope": "personal",
            },
        ),
        "work_logs": (
            {
                "title": "Helpdesk search XSS retest",
                "log_type": "VAPT",
                "content": (
                    "Verified contextual output encoding and confirmed the supplied search value "
                    "is rendered as text in the patched QA build."
                ),
                "evidence_url": "https://example.test/evidence/helpdesk-xss-retest",
                "risk_rating": "High",
                "days_ago": 5,
            },
        ),
        "reflections": (
            {
                "insight": "XSS testing depends on the output context, not only the input value.",
                "challenge": "Separating encoding controls from browser policy controls.",
                "next_step": "Compare HTML and attribute-context labs.",
                "days_ago": 1,
            },
        ),
    },
)

LAB_COMPLETIONS = (
    ("maya", "shared-htb-web-requests", 11),
    ("samira", "shared-htb-web-requests", 9),
    ("samira", "shared-pico-web-practice", 7),
    ("maya", "shared-thm-owasp", 5),
    ("maya", "shared-portswigger-sqli", 4),
    ("maya", "maya-portswigger-blind-sqli", 2),
    ("jordan", "jordan-thm-intro-siem", 3),
    ("samira", "samira-portswigger-xss", 1),
    ("jordan", "shared-thm-network-fundamentals", 8),
    ("samira", "shared-thm-defensive-security", 6),
    ("maya", "maya-portswigger-reset-logic", 1),
    ("jordan", "jordan-thm-networkminer", 2),
    ("samira", "samira-htb-linux-fundamentals", 3),
)

NOTE_ACCESS_REQUESTS = (
    {
        "topic": "maya-access-control",
        "status": "pending",
        "days_ago": 1,
    },
    {
        "topic": "jordan-siem-triage",
        "note": "jordan-siem-note",
        "status": "approved",
        "days_ago": 6,
        "responded_days_ago": 5,
    },
)


class DemoDataError(RuntimeError):
    """Raised when demo data cannot be inserted safely."""


def validate_demo_definition():
    """Check cross-record keys before opening a database transaction."""

    user_keys = {user["key"] for user in DEMO_USERS}
    emails = [user["email"] for user in DEMO_USERS]
    if len(user_keys) != len(DEMO_USERS) or len(set(emails)) != len(emails):
        raise DemoDataError("Demo user keys and emails must be unique.")

    vulnerability_codes = {item[0] for item in APP_VULNERABILITIES}
    threat_codes = {item[0] for item in THREAT_TACTICS}
    category_count = 0
    topic_keys = set()
    note_keys = set()
    lab_keys = set()

    for user in DEMO_USERS:
        try:
            validate_email(user["email"], check_deliverability=False)
            for contact in user["contacts"]:
                validate_email(contact["email"], check_deliverability=False)
        except EmailNotValidError as exc:
            raise DemoDataError(f"Invalid demo email address: {exc}") from exc

        if user["role"] not in {"user", "admin"}:
            raise DemoDataError(f"Unsupported role for {user['key']}.")
        category_names = [category["name"] for category in user["categories"]]
        if len(category_names) != len(set(category_names)):
            raise DemoDataError(f"Category names must be unique for {user['key']}.")

        for category in user["categories"]:
            category_count += 1
            for topic in category["topics"]:
                topic_key = topic["key"]
                note_key = topic["note"]["key"]
                if topic_key in topic_keys or note_key in note_keys:
                    raise DemoDataError("Topic and note keys must be globally unique.")
                topic_keys.add(topic_key)
                note_keys.add(note_key)

                for lab in topic["labs"]:
                    if lab["key"] in lab_keys:
                        raise DemoDataError("Lab keys must be globally unique.")
                    if lab["platform"] not in SUPPORTED_PLATFORM_SLUGS:
                        raise DemoDataError(f"Unknown lab platform: {lab['platform']}.")
                    expected_visibility = "public" if user["role"] == "admin" else "personal"
                    if lab["visibility"] != expected_visibility:
                        raise DemoDataError(
                            f"{lab['key']} must use {expected_visibility} visibility."
                        )
                    if lab["url"] not in topic["note"]["body"]:
                        raise DemoDataError(
                            f"{lab['key']} must be linked from its related note."
                        )
                    lab_keys.add(lab["key"])

        for finding in user["findings"]:
            if finding["vulnerability"] not in vulnerability_codes | {None}:
                raise DemoDataError(
                    f"Unknown vulnerability code: {finding['vulnerability']}."
                )
            if finding["threat"] not in threat_codes | {None}:
                raise DemoDataError(f"Unknown threat code: {finding['threat']}.")

    if category_count < 6:
        raise DemoDataError("The demo dataset must include at least six categories.")
    if len(lab_keys) < 10:
        raise DemoDataError("The demo dataset must include at least ten labs.")

    for user_key, lab_key, _days_ago in LAB_COMPLETIONS:
        if user_key not in user_keys or lab_key not in lab_keys:
            raise DemoDataError("A lab completion references an unknown demo key.")

    for request in NOTE_ACCESS_REQUESTS:
        note_key = request.get("note")
        if request["topic"] not in topic_keys or (
            note_key is not None and note_key not in note_keys
        ):
            raise DemoDataError("A note access request references an unknown demo key.")
        if request["status"] == "approved" and note_key is None:
            raise DemoDataError("An approved note access request requires a selected note.")


def validate_target(application, confirmed_database):
    """Refuse production, system databases, or a mistyped confirmation."""

    environment = os.getenv("APP_ENV", "development").strip().lower()
    database_name = str(application.config.get("DB_NAME", "")).strip()
    if environment == "production":
        raise DemoDataError("The demo injector is disabled when APP_ENV=production.")
    if not database_name or database_name.lower() in SYSTEM_DATABASES:
        raise DemoDataError("Choose a normal local or test application database.")
    if confirmed_database != database_name:
        raise DemoDataError(
            f"Database confirmation does not match DB_NAME '{database_name}'."
        )
    return database_name


def inject_demo_data(
    application,
    confirmed_database,
    password,
    replace=False,
    output=print,
):
    """Insert all demo records and return per-table insertion counts."""

    validate_target(application, confirmed_database)
    if not PASSWORD_MIN_LENGTH <= len(password) <= PASSWORD_MAX_LENGTH:
        raise DemoDataError(
            f"Demo password must contain {PASSWORD_MIN_LENGTH} to "
            f"{PASSWORD_MAX_LENGTH} characters."
        )

    validate_demo_definition()
    now = datetime.now().replace(microsecond=0)
    counts = Counter()

    with application.app_context():
        output("Preparing reference catalogs...")
        seed_database(output=lambda _message: None, application=application)
        with transaction() as cursor:
            database = db.using(cursor)
            known_demo_emails = [
                *(user["email"] for user in DEMO_USERS),
                *LEGACY_DEMO_EMAILS,
            ]
            existing_users = (
                database.table("users")
                .select("id", "email")
                .where_in("email", known_demo_emails)
                .all()
            )
            if existing_users and not replace:
                raise DemoDataError(
                    "Demo users already exist. Run again with --replace to refresh them."
                )
            if replace:
                _remove_existing_demo_data(database, existing_users)

            platform_ids = {
                slug: _required_id(database, "lab_platforms", "slug", slug)
                for slug in SUPPORTED_PLATFORM_SLUGS
            }
            vulnerability_ids = {
                code: _required_id(database, "vulnerability_catalog", "code", code)
                for code in {item["vulnerability"] for user in DEMO_USERS for item in user["findings"]}
                if code
            }
            threat_ids = {
                code: _required_id(database, "threat_catalog", "code", code)
                for code in {item["threat"] for user in DEMO_USERS for item in user["findings"]}
                if code
            }

            user_ids = {}
            topic_ids = {}
            note_ids = {}
            lab_ids = {}
            disabled_mfa_secret = None

            output("Creating demo accounts...")
            for user_index, user in enumerate(DEMO_USERS):
                output(f"  account: {user['email']}")
                created_at = now - timedelta(days=70 - (user_index * 5))
                user_ids[user["key"]] = _insert(
                    database,
                    counts,
                    "users",
                    {
                        "email": user["email"],
                        "password_hash": hash_password(password),
                        "display_name": user["display_name"],
                        "role": user["role"],
                        "is_banned": False,
                        "mfa_secret": disabled_mfa_secret,
                        "mfa_enabled": False,
                        "auth_version": 0,
                        "failed_login_count": 0,
                        "last_failed_login_at": None,
                        "locked_until": None,
                        "profile_bio": user["bio"],
                        "profile_image": None,
                        "created_at": created_at,
                        "updated_at": now - timedelta(days=user_index),
                    },
                )

            for user in DEMO_USERS:
                output(f"Creating linked learning data for {user['display_name']}...")
                owner_id = user_ids[user["key"]]
                for category_index, category in enumerate(user["categories"]):
                    category_id = _insert(
                        database,
                        counts,
                        "categories",
                        {
                            "name": category["name"],
                            "description": category["description"],
                            "color": category["color"],
                            "is_deleted": False,
                            "owner_id": owner_id,
                            "created_at": now - timedelta(days=45 - category_index),
                            "updated_at": now - timedelta(days=category_index + 2),
                        },
                    )

                    for topic_index, topic in enumerate(category["topics"]):
                        topic_id = _insert(
                            database,
                            counts,
                            "topics",
                            {
                                "title": topic["title"],
                                "slug": topic["key"],
                                "description": topic["description"],
                                "status": topic["status"],
                                "priority": topic["priority"],
                                "notes": topic["summary"],
                                "is_deleted": False,
                                "category_id": category_id,
                                "owner_id": owner_id,
                                "created_at": now - timedelta(days=35 - topic_index),
                                "updated_at": now - timedelta(days=topic_index + 1),
                            },
                        )
                        topic_ids[topic["key"]] = topic_id

                        note = topic["note"]
                        note_id = _insert(
                            database,
                            counts,
                            "notes",
                            {
                                "title": note["title"],
                                "body": note["body"],
                                "topic_id": topic_id,
                                "owner_id": owner_id,
                                "is_deleted": False,
                                "created_at": now - timedelta(days=25 - topic_index),
                                "updated_at": now - timedelta(days=topic_index),
                            },
                        )
                        note_ids[note["key"]] = note_id

                        for lab_index, lab in enumerate(topic["labs"]):
                            related_note = f"Related note: {note['title']}."
                            lab_id = _insert(
                                database,
                                counts,
                                "lab_references",
                                {
                                    "name": lab["name"],
                                    "platform_id": platform_ids[lab["platform"]],
                                    "url": lab["url"],
                                    "notes": f"{lab['notes']}\n\n{related_note}",
                                    "topic_id": topic_id,
                                    "owner_id": owner_id,
                                    "visibility": lab["visibility"],
                                    "is_deleted": False,
                                    "created_at": now
                                    - timedelta(days=20 - topic_index - lab_index),
                                    "updated_at": now
                                    - timedelta(days=topic_index + lab_index),
                                },
                            )
                            lab_ids[lab["key"]] = lab_id

                _insert_contacts(database, counts, user, owner_id, now)
                _insert_findings(
                    database,
                    counts,
                    user,
                    owner_id,
                    vulnerability_ids,
                    threat_ids,
                    now,
                )
                _insert_tasks(database, counts, user, owner_id, now)
                _insert_work_logs(database, counts, user, owner_id, now)
                _insert_reflections(database, counts, user, owner_id, now)
                _insert_activity(database, counts, user, owner_id, now)
                _insert_audit_history(database, counts, user, owner_id, now)

            output("Creating cross-account progress and access-request data...")
            output("  roadmap items")
            _insert_roadmap_items(database, counts, user_ids, topic_ids, now)
            output("  lab completions")
            _insert_lab_completions(database, counts, user_ids, lab_ids, now)
            output("  note access requests")
            _insert_note_access_requests(
                database,
                counts,
                user_ids["admin"],
                topic_ids,
                note_ids,
                now,
            )
            output("  pending vulnerability suggestion")
            _insert_pending_vulnerability(
                database,
                counts,
                user_ids["samira"],
                now,
            )

    output("Demo data inserted successfully.")
    return dict(sorted(counts.items()))


def _remove_existing_demo_data(database, existing_users):
    for row in existing_users:
        user_id = int(row["id"])
        database.table("note_access_requests").where(
            "requester_admin_id", "=", user_id
        ).delete()
        database.table("scheduled_tasks").where("user_id", "=", user_id).delete()
        database.table("scheduled_tasks").where("created_by", "=", user_id).delete()
        database.table("audit_logs").where("user_id", "=", user_id).delete()
        database.table("activity_events").where("owner_id", "=", user_id).delete()
        database.table("security_findings").where("owner_id", "=", user_id).delete()

    database.table("vulnerability_catalog").where(
        "code", "=", DEMO_SUGGESTION_CODE
    ).delete()

    for row in existing_users:
        database.table("users").where("id", "=", int(row["id"])).delete()


def _required_id(database, table, column, value):
    row = database.table(table).select("id").where(column, "=", value).first()
    if not row:
        raise DemoDataError(f"Required reference {table}.{column}={value!r} is missing.")
    return int(row["id"])


def _insert(database, counts, table, values):
    result = database.table(table).insert(values)
    counts[table] += 1
    return int(result.last_insert_id)


def _insert_contacts(database, counts, user, owner_id, now):
    for index, contact in enumerate(user["contacts"]):
        _insert(
            database,
            counts,
            "contacts",
            {
                **contact,
                "is_deleted": False,
                "owner_id": owner_id,
                "created_at": now - timedelta(days=18 - index),
                "updated_at": now - timedelta(days=3),
            },
        )


def _insert_findings(
    database,
    counts,
    user,
    owner_id,
    vulnerability_ids,
    threat_ids,
    now,
):
    for finding in user["findings"]:
        detected_at = now - timedelta(days=finding["days_ago"], hours=2)
        _insert(
            database,
            counts,
            "security_findings",
            {
                "owner_id": owner_id,
                "vulnerability_id": vulnerability_ids.get(finding["vulnerability"]),
                "threat_id": threat_ids.get(finding["threat"]),
                "activity_type": finding["activity_type"],
                "title": finding["title"],
                "target": finding["target"],
                "severity": finding["severity"],
                "status": finding["status"],
                "evidence": finding["evidence"],
                "notes": finding["notes"],
                "detected_at": detected_at,
                "is_deleted": False,
                "created_at": detected_at,
                "updated_at": detected_at + timedelta(hours=4),
            },
        )


def _insert_tasks(database, counts, user, owner_id, now):
    for index, task in enumerate(user["tasks"]):
        created_at = now - timedelta(days=12 - index)
        _insert(
            database,
            counts,
            "scheduled_tasks",
            {
                "user_id": owner_id if task["scope"] == "personal" else None,
                "created_by": owner_id,
                "title": task["title"],
                "description": task["description"],
                "task_type": task["task_type"],
                "due_at": now + timedelta(days=task["days_due"]),
                "status": task["status"],
                "scope": task["scope"],
                "created_at": created_at,
                "updated_at": now - timedelta(days=max(task["days_due"] * -1, 0)),
            },
        )


def _insert_work_logs(database, counts, user, owner_id, now):
    for work_log in user["work_logs"]:
        log_date = (now - timedelta(days=work_log["days_ago"])).date()
        _insert(
            database,
            counts,
            "work_logs",
            {
                "title": work_log["title"],
                "log_type": work_log["log_type"],
                "content": work_log["content"],
                "evidence_url": work_log["evidence_url"],
                "risk_rating": work_log["risk_rating"],
                "log_date": log_date,
                "owner_id": owner_id,
                "created_at": datetime.combine(log_date, datetime.min.time()),
                "updated_at": datetime.combine(log_date, datetime.min.time())
                + timedelta(hours=2),
            },
        )


def _insert_reflections(database, counts, user, owner_id, now):
    for reflection in user["reflections"]:
        created_at = now - timedelta(days=reflection["days_ago"])
        _insert(
            database,
            counts,
            "progress_reflections",
            {
                "insight": reflection["insight"],
                "challenge": reflection["challenge"],
                "next_step": reflection["next_step"],
                "owner_id": owner_id,
                "created_at": created_at,
                "updated_at": created_at,
            },
        )


def _insert_activity(database, counts, user, owner_id, now):
    event_types = (
        ("topic_progress", 2),
        ("note_review", 2),
        ("lab_practice", 4),
        ("finding_update", 3),
    )
    event_count = 8 if user["role"] == "admin" else 14
    for index in range(event_count):
        event_type, base_intensity = event_types[index % len(event_types)]
        occurred_on = (now - timedelta(days=(index * 2) + (owner_id % 3))).date()
        _insert(
            database,
            counts,
            "activity_events",
            {
                "event_type": event_type,
                "intensity": min(5, base_intensity + (index % 2)),
                "occurred_on": occurred_on,
                "owner_id": owner_id,
                "created_at": datetime.combine(occurred_on, datetime.min.time())
                + timedelta(hours=18),
                "updated_at": datetime.combine(occurred_on, datetime.min.time())
                + timedelta(hours=18),
            },
        )


def _insert_audit_history(database, counts, user, owner_id, now):
    actions = (
        ("login", f"{user['display_name']} signed in to the demo workspace."),
        ("topic_created", f"{user['display_name']} added a learning topic."),
        ("note_created", f"{user['display_name']} saved a linked study note."),
        ("lab_completed", f"{user['display_name']} updated lab progress."),
    )
    for index, (action, details) in enumerate(actions):
        _insert(
            database,
            counts,
            "audit_logs",
            {
                "action": action,
                "details": details,
                "ip_address": f"192.0.2.{20 + (owner_id % 200)}",
                "user_id": owner_id,
                "created_at": now - timedelta(days=index * 2, hours=index),
            },
        )


def _insert_roadmap_items(database, counts, user_ids, topic_ids, now):
    items = (
        ("maya", "SQL Injection Verification", "Complete blind SQLi practice", "in-progress", 14),
        ("maya", "Access Control Testing", "Retest object ownership", "planned", 21),
        ("jordan", "SIEM Alert Triage", "Publish triage worksheet", "in-progress", 10),
        ("jordan", "Credential Access Triage", "Validate spray detection", "planned", 18),
        ("samira", "Linux Command-Line Fundamentals", "Finish Part 1", "in-progress", 7),
        ("samira", "Reflected Cross-Site Scripting", "Compare output contexts", "planned", 15),
    )
    topic_key_by_title = {
        topic["title"]: topic["key"]
        for user in DEMO_USERS
        for category in user["categories"]
        for topic in category["topics"]
    }
    for user_key, title, milestone, status, days_due in items:
        _insert(
            database,
            counts,
            "roadmap_items",
            {
                "title": title,
                "milestone": milestone,
                "status": status,
                "due_date": (now + timedelta(days=days_due)).date(),
                "topic_id": topic_ids[topic_key_by_title[title]],
                "owner_id": user_ids[user_key],
                "created_at": now - timedelta(days=20),
                "updated_at": now - timedelta(days=1),
            },
        )


def _insert_lab_completions(database, counts, user_ids, lab_ids, now):
    for user_key, lab_key, days_ago in LAB_COMPLETIONS:
        _insert(
            database,
            counts,
            "lab_completions",
            {
                "lab_id": lab_ids[lab_key],
                "user_id": user_ids[user_key],
                "completed_at": now - timedelta(days=days_ago),
            },
        )


def _insert_note_access_requests(
    database,
    counts,
    admin_id,
    topic_ids,
    note_ids,
    now,
):
    for request in NOTE_ACCESS_REQUESTS:
        requested_at = now - timedelta(days=request["days_ago"])
        responded_days_ago = request.get("responded_days_ago")
        responded_at = (
            now - timedelta(days=responded_days_ago)
            if responded_days_ago is not None
            else None
        )
        request_id = _insert(
            database,
            counts,
            "note_access_requests",
            {
                "topic_id": topic_ids[request["topic"]],
                "requester_admin_id": admin_id,
                "status": request["status"],
                "requested_at": requested_at,
                "responded_at": responded_at,
            },
        )
        if request["status"] == "approved":
            database.table("note_access_grants").insert(
                {
                    "request_id": request_id,
                    "note_id": note_ids[request["note"]],
                    "granted_at": responded_at or requested_at,
                },
            )
            counts["note_access_grants"] += 1


def _insert_pending_vulnerability(database, counts, creator_id, now):
    _insert(
        database,
        counts,
        "vulnerability_catalog",
        {
            "code": DEMO_SUGGESTION_CODE,
            "name": "Inconsistent Security Header Policy",
            "category": "User submitted",
            "default_severity": "medium",
            "description": (
                "Synthetic suggestion to review inconsistent CSP and frame-protection headers "
                "across application routes."
            ),
            "source": "Cyber Dashboard demo dataset",
            "approval_status": "pending",
            "is_active": False,
            "created_by_user_id": creator_id,
            "reviewed_by_user_id": None,
            "reviewed_at": None,
            "created_at": now - timedelta(days=1),
            "updated_at": now - timedelta(days=1),
        },
    )


def build_parser():
    parser = argparse.ArgumentParser(
        description="Insert correlated, realistic Cyber Dashboard demo records."
    )
    parser.add_argument(
        "--confirm-db",
        required=True,
        help="Must exactly match the configured DB_NAME.",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Remove only the previous fixed demo accounts and recreate their records.",
    )
    parser.add_argument(
        "--password",
        help=(
            "Shared password for the generated accounts. A strong random password is "
            "generated and printed when omitted."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate configuration and dataset relationships without writing records.",
    )
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        application = create_app()
        database_name = validate_target(application, args.confirm_db)
        validate_demo_definition()
        if args.dry_run:
            print(f"Demo definition is valid for database '{database_name}'.")
            return 0

        password = args.password or secrets.token_urlsafe(18)
        counts = inject_demo_data(
            application,
            confirmed_database=args.confirm_db,
            password=password,
            replace=args.replace,
        )
    except (DatabaseError, DemoDataError, RuntimeError, ValueError) as exc:
        print(f"[FAIL] Demo data was not inserted: {exc}", file=sys.stderr)
        return 1

    print(f"Target database: {database_name}")
    print("Created demo accounts:")
    for user in DEMO_USERS:
        print(f"  {user['role']:5}  {user['email']}")
    print(f"Shared password: {password}")
    print("Inserted records:")
    for table, count in counts.items():
        print(f"  {table}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
