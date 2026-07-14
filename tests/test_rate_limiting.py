"""Rate-limit contracts run with Flask-Limiter enabled."""

from app.services.auth_service import LoginDecision


def test_login_is_rate_limited_by_account(monkeypatch, rate_limited_client):
    monkeypatch.setattr(
        "app.controllers.auth_controller.auth_service.authenticate",
        lambda *args, **kwargs: LoginDecision("invalid"),
    )

    responses = [
        rate_limited_client.post(
            "/auth/login",
            data={"email": "limited@example.com", "password": "WrongPassword123!"},
        )
        for _attempt in range(9)
    ]

    assert all(response.status_code == 200 for response in responses[:8])
    assert responses[8].status_code == 429
