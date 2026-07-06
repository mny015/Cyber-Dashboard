from werkzeug.security import check_password_hash

from utils.db import execute, fetch_one


def test_admin_can_reset_another_users_password(admin_client, user_factory):
    user = user_factory(password="OldPassword123!")

    response = admin_client.post(
        f"/admin/users/{user['id']}/password",
        data={
            "password": "NewPassword123!",
            "confirm_password": "NewPassword123!",
        },
        follow_redirects=True,
    )

    updated = fetch_one("SELECT password_hash, auth_version FROM users WHERE id = %s", (user["id"],))

    assert response.status_code == 200
    assert b"Password updated" in response.data
    assert check_password_hash(updated["password_hash"], "NewPassword123!")
    assert updated["auth_version"] == user["auth_version"] + 1


def test_normal_user_cannot_reset_another_users_password(authenticated_client, user_factory):
    user = user_factory(password="OldPassword123!")

    response = authenticated_client.post(
        f"/admin/users/{user['id']}/password",
        data={
            "password": "NewPassword123!",
            "confirm_password": "NewPassword123!",
        },
    )

    unchanged = fetch_one("SELECT password_hash FROM users WHERE id = %s", (user["id"],))

    assert response.status_code == 403
    assert check_password_hash(unchanged["password_hash"], "OldPassword123!")


def test_admin_can_ban_and_unban_user(admin_client, user_factory):
    user = user_factory()

    ban_response = admin_client.post(f"/admin/users/{user['id']}/ban", follow_redirects=True)
    banned = fetch_one("SELECT is_banned FROM users WHERE id = %s", (user["id"],))

    unban_response = admin_client.post(f"/admin/users/{user['id']}/unban", follow_redirects=True)
    unbanned = fetch_one("SELECT is_banned FROM users WHERE id = %s", (user["id"],))

    assert ban_response.status_code == 200
    assert banned["is_banned"] == 1
    assert unban_response.status_code == 200
    assert unbanned["is_banned"] == 0


def test_admin_can_delete_user_and_preserve_audit_history(admin_client, user_factory):
    user = user_factory()
    audit_details = f"temporary audit row {user['id']}"
    execute(
        """
        INSERT INTO audit_logs (action, details, ip_address, user_id, created_at)
        VALUES ('test_action', %s, '127.0.0.1', %s, NOW())
        """,
        (audit_details, user["id"]),
    )

    try:
        response = admin_client.post(f"/admin/users/{user['id']}/delete", follow_redirects=True)
        deleted = fetch_one("SELECT id FROM users WHERE id = %s", (user["id"],))
        retained_log = fetch_one(
            """
            SELECT user_id
            FROM audit_logs
            WHERE action = 'test_action' AND details = %s
            """,
            (audit_details,),
        )

        assert response.status_code == 200
        assert b"was deleted" in response.data
        assert deleted is None
        assert retained_log["user_id"] is None
    finally:
        execute("DELETE FROM audit_logs WHERE action = 'test_action' AND details = %s", (audit_details,))
