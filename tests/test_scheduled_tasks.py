def test_user_can_create_and_view_own_scheduled_task(authenticated_client):
    response = authenticated_client.post(
        "/scheduled-tasks/",
        data={
            "title": "Review notes",
            "description": "Check yesterday's learning notes",
            "task_type": "note",
            "due_at": "2026-07-05T09:00",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Review notes" in response.data


def test_user_cannot_modify_another_users_private_task(
    client, user_factory, login_as, database
):
    owner = user_factory(display_name="Task Owner")
    viewer = user_factory(display_name="Task Viewer")
    _, task_id = database.execute(
        """
        INSERT INTO scheduled_tasks
            (user_id, created_by, title, description, task_type, due_at,
             status, scope, created_at, updated_at)
        VALUES (%s, %s, 'Private task', '', 'general', NULL,
                'upcoming', 'personal', NOW(), NOW())
        """,
        (owner["id"], owner["id"]),
    )

    login_as(client, viewer)
    response = client.post(f"/scheduled-tasks/{task_id}/complete")

    assert response.status_code == 403
    task = database.fetch_one("SELECT status FROM scheduled_tasks WHERE id = %s", (task_id,))
    assert task["status"] == "upcoming"


def test_admin_can_view_global_scheduled_tasks(admin_client, admin_user, database):
    database.execute(
        """
        INSERT INTO scheduled_tasks
            (user_id, created_by, title, description, task_type, due_at,
             status, scope, created_at, updated_at)
        VALUES (NULL, %s, 'Review shared labs', '', 'lab', NULL,
                'upcoming', 'global', NOW(), NOW())
        """,
        (admin_user["id"],),
    )

    response = admin_client.get("/scheduled-tasks/")

    assert response.status_code == 200
    assert b"Review shared labs" in response.data


def test_mark_scheduled_task_completed(authenticated_client, test_user, database):
    _, task_id = database.execute(
        """
        INSERT INTO scheduled_tasks
            (user_id, created_by, title, description, task_type, due_at,
             status, scope, created_at, updated_at)
        VALUES (%s, %s, 'Complete lab writeup', '', 'lab', NULL,
                'upcoming', 'personal', NOW(), NOW())
        """,
        (test_user["id"], test_user["id"]),
    )

    response = authenticated_client.post(f"/scheduled-tasks/{task_id}/complete", follow_redirects=True)

    assert response.status_code == 200
    assert b"Task marked complete." in response.data
    task = database.fetch_one("SELECT status FROM scheduled_tasks WHERE id = %s", (task_id,))
    assert task["status"] == "completed"
