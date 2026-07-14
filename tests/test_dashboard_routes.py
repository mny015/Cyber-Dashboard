def test_authenticated_user_can_load_user_dashboard(authenticated_client):
    response = authenticated_client.get("/user/dashboard")

    assert response.status_code == 200
    assert b"Cyber Dashboard" in response.data


def test_unauthenticated_user_is_redirected_from_dashboard(client):
    response = client.get("/dashboard")

    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_normal_user_cannot_access_admin_dashboard(authenticated_client):
    response = authenticated_client.get("/admin/dashboard")

    assert response.status_code == 403


def test_admin_can_load_admin_dashboard(admin_client):
    response = admin_client.get("/admin/dashboard")

    assert response.status_code == 200
    assert b"Cyber Dashboard Admin" in response.data


def test_user_dashboard_contains_requested_panels(authenticated_client):
    response = authenticated_client.get("/user/dashboard")

    assert response.status_code == 200
    assert b"Recent Changes" in response.data
    assert b"Rooms Completed" in response.data
    assert b"Scheduled" in response.data
    assert b"Last done" in response.data


def test_admin_dashboard_contains_requested_panels(admin_client):
    response = admin_client.get("/admin/dashboard")

    assert response.status_code == 200
    assert b"Platform Changes" in response.data
    assert b"Shared Labs" in response.data
    assert b"Users" in response.data
    assert b"Requests" in response.data
    assert b"Audit Logs" in response.data


def test_user_dashboard_does_not_expose_other_users_private_note_content(
    client, user_factory, login_as, database
):
    note_owner = user_factory(display_name="Private Note Owner")
    viewer = user_factory(display_name="Dashboard Viewer")
    private_body = "PRIVATE-NOTE-BODY-SHOULD-NOT-APPEAR"
    private_title = "Private Dashboard Note"

    database.execute(
        """
        INSERT INTO notes (title, body, topic_id, owner_id, is_deleted, created_at, updated_at)
        VALUES (%s, %s, NULL, %s, 0, NOW(), NOW())
        """,
        (private_title, private_body, note_owner["id"]),
    )

    login_as(client, viewer)
    user_response = client.get("/user/dashboard")
    assert user_response.status_code == 200
    assert private_title.encode() not in user_response.data
    assert private_body.encode() not in user_response.data


def test_admin_dashboard_does_not_expose_private_note_bodies(
    admin_client, user_factory, database
):
    note_owner = user_factory(display_name="Private Note Owner")
    private_body = "PRIVATE-NOTE-BODY-SHOULD-NOT-APPEAR"
    private_title = "Private Dashboard Note"

    database.execute(
        """
        INSERT INTO notes (title, body, topic_id, owner_id, is_deleted, created_at, updated_at)
        VALUES (%s, %s, NULL, %s, 0, NOW(), NOW())
        """,
        (private_title, private_body, note_owner["id"]),
    )

    admin_response = admin_client.get("/admin/dashboard")
    assert admin_response.status_code == 200
    assert private_title.encode() not in admin_response.data
    assert private_body.encode() not in admin_response.data


def test_dashboard_handles_empty_user_data_without_crashing(client, user_factory, login_as):
    empty_user = user_factory(display_name="Empty Dashboard User")
    login_as(client, empty_user)

    response = client.get("/user/dashboard")

    assert response.status_code == 200
    assert b"No recent changes" in response.data
    assert b"0/" in response.data
