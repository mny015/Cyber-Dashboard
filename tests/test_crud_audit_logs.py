from uuid import uuid4

from app.utils.validation import slugify


def audit_rows_for(database, user_id, prefix):
    return database.fetch_all(
        """
        SELECT action, details
        FROM audit_logs
        WHERE user_id = %s AND action LIKE %s
        ORDER BY id ASC
        """,
        (user_id, f"{prefix}_%"),
    )


def test_topic_crud_writes_audit_logs(authenticated_client, test_user, database):
    suffix = uuid4().hex[:10]
    title = f"Audit Topic {suffix}"

    create_response = authenticated_client.post(
        "/topics/new",
        data={
            "title": title,
            "description": "Topic audit coverage",
            "status": "planned",
            "priority": "medium",
            "notes": "Created by route test",
            "category_id": "",
        },
    )
    topic = database.fetch_one(
        "SELECT id FROM topics WHERE owner_id = %s AND title = %s",
        (test_user["id"], title),
    )

    update_response = authenticated_client.post(
        f"/topics/{topic['id']}/edit",
        data={
            "title": f"{title} Updated",
            "description": "Updated topic audit coverage",
            "status": "in-progress",
            "priority": "high",
            "notes": "Updated by route test",
            "category_id": "",
        },
    )
    delete_response = authenticated_client.post(f"/topics/{topic['id']}/delete")

    actions = [
        row["action"] for row in audit_rows_for(database, test_user["id"], "topic")
    ]

    assert create_response.status_code == 302
    assert update_response.status_code == 302
    assert delete_response.status_code == 302
    assert actions[-3:] == ["topic_created", "topic_updated", "topic_deleted"]


def test_category_crud_writes_audit_logs(authenticated_client, test_user, database):
    suffix = uuid4().hex[:10]
    name = f"Audit Category {suffix}"

    create_response = authenticated_client.post(
        "/categories/new",
        data={
            "name": name,
            "description": "Category audit coverage",
            "color": "#1677ff",
        },
    )
    category = database.fetch_one(
        "SELECT id FROM categories WHERE owner_id = %s AND name = %s",
        (test_user["id"], name),
    )

    update_response = authenticated_client.post(
        f"/categories/{category['id']}/edit",
        data={
            "name": f"{name} Updated",
            "description": "Updated category audit coverage",
            "color": "#06b6d4",
        },
    )
    delete_response = authenticated_client.post(f"/categories/{category['id']}/delete")

    actions = [
        row["action"] for row in audit_rows_for(database, test_user["id"], "category")
    ]

    assert create_response.status_code == 302
    assert update_response.status_code == 302
    assert delete_response.status_code == 302
    assert actions[-3:] == ["category_created", "category_updated", "category_deleted"]


def test_note_crud_writes_audit_logs_without_leaking_note_content(
    authenticated_client, test_user, database
):
    suffix = uuid4().hex[:10]
    topic_title = f"Note Audit Topic {suffix}"
    _, topic_id = database.execute(
        """
        INSERT INTO topics
            (title, slug, description, status, priority, notes, is_deleted,
             category_id, owner_id, created_at, updated_at)
        VALUES (%s, %s, %s, 'planned', 'medium', '', 0, NULL, %s, NOW(), NOW())
        """,
        (topic_title, slugify(topic_title), "Topic for note audit logs", test_user["id"]),
    )

    create_response = authenticated_client.post(
        "/notes/new",
        data={
            "title": f"Private Audit Note {suffix}",
            "body": "Secret note body should not appear in audit logs.",
            "topic_id": topic_id,
        },
    )
    note = database.fetch_one(
        "SELECT id FROM notes WHERE owner_id = %s AND topic_id = %s",
        (test_user["id"], topic_id),
    )

    update_response = authenticated_client.post(
        f"/notes/{note['id']}/edit",
        data={
            "title": f"Private Audit Note {suffix} Updated",
            "body": "Updated secret note body should not appear in audit logs.",
            "topic_id": topic_id,
        },
    )
    delete_response = authenticated_client.post(f"/notes/{note['id']}/delete")

    rows = audit_rows_for(database, test_user["id"], "note")
    actions = [row["action"] for row in rows]
    details = " ".join(row["details"] for row in rows)

    assert create_response.status_code == 302
    assert update_response.status_code == 302
    assert delete_response.status_code == 302
    assert actions[-3:] == ["note_created", "note_updated", "note_deleted"]
    assert "Private Audit Note" not in details
    assert "Secret note body" not in details


def test_contact_crud_writes_audit_logs_without_leaking_contact_details(
    authenticated_client, test_user, database
):
    suffix = uuid4().hex[:10]
    email = f"audit-contact-{suffix}@example.com"

    create_response = authenticated_client.post(
        "/contacts/new",
        data={
            "name": f"Audit Contact {suffix}",
            "email": email,
            "phone": "+1 555 010 4444",
            "notes": "Private contact note",
        },
    )
    contact = database.fetch_one(
        "SELECT id FROM contacts WHERE owner_id = %s AND email = %s",
        (test_user["id"], email),
    )

    update_response = authenticated_client.post(
        f"/contacts/{contact['id']}/edit",
        data={
            "name": f"Audit Contact {suffix} Updated",
            "email": email,
            "phone": "+1 555 010 5555",
            "notes": "Updated private contact note",
        },
    )
    delete_response = authenticated_client.post(f"/contacts/{contact['id']}/delete")

    rows = audit_rows_for(database, test_user["id"], "contact")
    actions = [row["action"] for row in rows]
    details = " ".join(row["details"] for row in rows)

    assert create_response.status_code == 302
    assert update_response.status_code == 302
    assert delete_response.status_code == 302
    assert actions[-3:] == ["contact_created", "contact_updated", "contact_deleted"]
    assert email not in details
    assert "+1 555" not in details
    assert "Private contact note" not in details
