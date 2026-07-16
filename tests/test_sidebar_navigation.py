"""Contracts for the authenticated application sidebar."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATIC_IMAGE_DIR = PROJECT_ROOT / "app" / "static" / "image"


def test_sidebar_uses_high_contrast_navigation_assets_for_both_themes():
    expected_assets = {
        "Dashboard-dark.png",
        "Topic-dark.png",
        "Notes-dark.png",
        "Labs-dark.png",
        "Schedule-dark.png",
        "Security_Findings-dark.png",
        "Categories-dark.png",
        "UserAdmin-dark.png",
        "Notifications-dark.png",
    }
    macro_source = (
        PROJECT_ROOT / "app" / "templates" / "macros" / "navigation.html"
    ).read_text(encoding="utf-8")
    base_source = (PROJECT_ROOT / "app" / "templates" / "base.html").read_text(
        encoding="utf-8"
    )

    for filename in expected_assets:
        assert (STATIC_IMAGE_DIR / filename).is_file()
        assert filename in base_source

    assert "sidebar-icon-light" not in macro_source
    assert "sidebar-icon-dark" not in macro_source
    assert "light_icon" not in macro_source
    assert "dark_icon" not in macro_source


def test_collapsed_sidebar_uses_centered_brand_mark():
    base_source = (PROJECT_ROOT / "app" / "templates" / "base.html").read_text(
        encoding="utf-8"
    )
    stylesheet = (
        PROJECT_ROOT / "app" / "static" / "css" / "sidebar.css"
    ).read_text(encoding="utf-8")

    assert 'class="sidebar-brand-mark"' in base_source
    assert "image/Favicon.png" in base_source
    assert "html.sidebar-collapsed .sidebar-brand-mark" in stylesheet
    assert "transform: translate(-50%, -50%);" in stylesheet


def test_sidebar_has_persistent_and_accessible_controls():
    base_source = (PROJECT_ROOT / "app" / "templates" / "base.html").read_text(
        encoding="utf-8"
    )
    javascript = (PROJECT_ROOT / "app" / "static" / "js" / "main.js").read_text(
        encoding="utf-8"
    )
    early_script = (
        PROJECT_ROOT / "app" / "static" / "js" / "theme.js"
    ).read_text(encoding="utf-8")

    assert 'id="app-sidebar"' in base_source
    assert "data-sidebar-toggle" in base_source
    assert "data-sidebar-mobile-toggle" in base_source
    assert 'aria-label="Collapse navigation"' in base_source
    assert 'aria-label="Application navigation"' in base_source
    assert 'localStorage.setItem("cyber-dashboard-sidebar"' in javascript
    assert 'localStorage.getItem("cyber-dashboard-sidebar")' in early_script


def test_public_pages_keep_the_compact_header(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b'class="site-header"' in response.data
    assert b'id="app-sidebar"' not in response.data
    assert b"data-sidebar-mobile-toggle" not in response.data
