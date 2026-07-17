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
