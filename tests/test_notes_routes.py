from uuid import uuid4

from utils.db import execute


def create_topic(user_id):
    slug = f"notes-topic-{uuid4().hex[:10]}"
    _, topic_id = execute(
        """
        INSERT INTO topics
            (title, slug, description, status, priority, notes, is_deleted,
             category_id, owner_id, created_at, updated_at)
        VALUES (%s, %s, %s, 'in-progress', 'medium', '', 0, NULL, %s, NOW(), NOW())
        """,
        ("Notes Topic", slug, "Topic for notes route tests", user_id),
    )
    return topic_id


def create_note(user_id, topic_id, title="Professional Notes", body="payload checklist"):
    _, note_id = execute(
        """
        INSERT INTO notes
            (title, body, topic_id, owner_id, is_deleted, created_at, updated_at)
        VALUES (%s, %s, %s, %s, 0, NOW(), NOW())
        """,
        (title, body, topic_id, user_id),
    )
    return note_id


def test_notes_index_supports_search_and_topic_filter(client, test_user, login_as):
    topic_id = create_topic(test_user["id"])
    create_note(test_user["id"], topic_id, body="payload checklist and commands")
    login_as(client, test_user)

    response = client.get(f"/notes/?q=payload&topic_id={topic_id}")

    assert response.status_code == 200
    assert b"Professional Notes" in response.data
    assert b"notes-command-bar" in response.data


def test_note_editor_renders_live_preview_shell(authenticated_client):
    response = authenticated_client.get("/notes/new")

    assert response.status_code == 200
    assert b"data-note-editor" in response.data
    assert b"data-note-preview" in response.data


def test_note_detail_renders_reader_hook(client, test_user, login_as):
    topic_id = create_topic(test_user["id"])
    note_id = create_note(test_user["id"], topic_id, body="## Finding\\n- Validate output")
    login_as(client, test_user)

    response = client.get(f"/notes/{note_id}")

    assert response.status_code == 200
    assert b"note-reader-card" in response.data
    assert b"data-note-render" in response.data
