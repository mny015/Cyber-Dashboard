from uuid import uuid4


def get_vulnerability(database):
    return database.fetch_one("SELECT id FROM vulnerability_catalog ORDER BY id LIMIT 1")


def get_threat(database):
    return database.fetch_one("SELECT id FROM threat_catalog ORDER BY id LIMIT 1")


def test_user_can_create_security_finding(client, test_user, login_as, database):
    vulnerability = get_vulnerability(database)
    threat = get_threat(database)
    login_as(client, test_user)

    response = client.post(
        "/security/new",
        data={
            "title": "IDOR tested on profile route",
            "activity_type": "vulnerability_tested",
            "severity": "high",
            "status": "testing",
            "vulnerability_id": vulnerability["id"],
            "threat_id": threat["id"],
            "target": "/profile",
            "evidence": "Verified owner checks.",
            "notes": "Needs regression coverage.",
        },
    )

    assert response.status_code == 302
    finding = database.fetch_one(
        """
        SELECT title, owner_id, severity, activity_type
        FROM security_findings
        WHERE owner_id = %s AND title = %s
        """,
        (test_user["id"], "IDOR tested on profile route"),
    )
    assert finding["severity"] == "high"
    assert finding["activity_type"] == "vulnerability_tested"


def test_admin_cannot_edit_user_private_security_finding(
    client, test_user, admin_user, login_as, database
):
    vulnerability = get_vulnerability(database)
    _, finding_id = database.execute(
        """
        INSERT INTO security_findings
            (owner_id, vulnerability_id, threat_id, activity_type, title,
             target, severity, status, evidence, notes, detected_at,
             is_deleted, created_at, updated_at)
        VALUES (%s, %s, NULL, 'vulnerability_found', 'Private finding',
                '/private', 'critical', 'open', '', '', NOW(), 0, NOW(), NOW())
        """,
        (test_user["id"], vulnerability["id"]),
    )
    login_as(client, admin_user)

    response = client.get(f"/security/{finding_id}/edit")

    assert response.status_code == 404


def test_user_suggestion_waits_for_admin_approval(
    client, test_user, login_as, database
):
    suggestion_name = f"Suggested vuln {uuid4().hex[:8]}"
    login_as(client, test_user)

    response = client.post(
        "/security/vulnerabilities/suggest",
        data={
            "name": suggestion_name,
            "category": "Cloud",
            "default_severity": "medium",
            "description": "Useful for cloud lab tracking.",
        },
    )

    assert response.status_code == 302
    suggestion = database.fetch_one(
        """
        SELECT approval_status, is_active
        FROM vulnerability_catalog
        WHERE created_by_user_id = %s AND name = %s
        """,
        (test_user["id"], suggestion_name),
    )
    assert suggestion["approval_status"] == "pending"
    assert suggestion["is_active"] == 0
