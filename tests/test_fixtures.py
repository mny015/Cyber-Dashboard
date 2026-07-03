def test_authenticated_client_fixture_reaches_dashboard(authenticated_client):
    response = authenticated_client.get("/dashboard")
    assert response.status_code == 302
    assert "/user/dashboard" in response.headers["Location"]


def test_admin_client_fixture_reaches_admin_dashboard(admin_client):
    response = admin_client.get("/dashboard")
    assert response.status_code == 302
    assert "/admin/dashboard" in response.headers["Location"]
