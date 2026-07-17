from werkzeug.security import check_password_hash


def test_admin_can_manage_user_accounts_and_preserve_audit_history(
    admin_client, user_factory, database
):
    user = user_factory(password="OldPassword123!")

    reset_response = admin_client.post(
        f"/admin/users/{user['id']}/password",
        data={
            "password": "NewPassword123!",
            "confirm_password": "NewPassword123!",
        },
        follow_redirects=True,
    )
    updated = database.fetch_one(
        "SELECT password_hash, auth_version FROM users WHERE id = %s",
        (user["id"],),
    )

    ban_response = admin_client.post(
        f"/admin/users/{user['id']}/ban", follow_redirects=True
    )
    banned = database.fetch_one(
        "SELECT is_banned FROM users WHERE id = %s", (user["id"],)
    )
    unban_response = admin_client.post(
        f"/admin/users/{user['id']}/unban", follow_redirects=True
    )
    unbanned = database.fetch_one(
        "SELECT is_banned FROM users WHERE id = %s", (user["id"],)
    )

    audit_details = f"temporary audit row {user['id']}"
    database.execute(
        """
        INSERT INTO audit_logs (action, details, ip_address, user_id, created_at)
        VALUES ('test_action', %s, '127.0.0.1', %s, NOW())
        """,
        (audit_details, user["id"]),
    )
    try:
        delete_response = admin_client.post(
            f"/admin/users/{user['id']}/delete", follow_redirects=True
        )
        deleted = database.fetch_one(
            "SELECT id FROM users WHERE id = %s", (user["id"],)
        )
        retained_log = database.fetch_one(
            """
            SELECT user_id
            FROM audit_logs
            WHERE action = 'test_action' AND details = %s
            """,
            (audit_details,),
        )

        assert reset_response.status_code == 200
        assert check_password_hash(updated["password_hash"], "NewPassword123!")
        assert updated["auth_version"] == user["auth_version"] + 1
        assert ban_response.status_code == 200
        assert banned["is_banned"] == 1
        assert unban_response.status_code == 200
        assert unbanned["is_banned"] == 0
        assert delete_response.status_code == 200
        assert deleted is None
        assert retained_log["user_id"] is None
    finally:
        database.execute(
            "DELETE FROM audit_logs WHERE action = 'test_action' AND details = %s",
            (audit_details,),
        )


def test_normal_user_cannot_reset_another_users_password(
    authenticated_client, user_factory, database
):
    user = user_factory(password="ProtectedPassword123!")

    response = authenticated_client.post(
        f"/admin/users/{user['id']}/password",
        data={
            "password": "ChangedPassword123!",
            "confirm_password": "ChangedPassword123!",
        },
    )
    unchanged = database.fetch_one(
        "SELECT password_hash FROM users WHERE id = %s", (user["id"],)
    )

    assert response.status_code == 403
    assert check_password_hash(unchanged["password_hash"], "ProtectedPassword123!")
