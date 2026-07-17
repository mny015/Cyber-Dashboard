import pytest
from cryptography.fernet import Fernet

from app import create_app
from app.extensions import csrf, login_manager
from config import DevelopmentConfig, ProductionConfig, TestingConfig, get_config


def test_testing_factory_initializes_security_extensions():
    app = create_app("testing")

    assert app.testing is True
    assert app.debug is False
    assert app.login_manager is login_manager
    assert app.extensions["csrf"] is csrf
    assert app.config["RATELIMIT_ENABLED"] is False

    response = app.test_client().get("/api/ping")
    assert response.status_code == 200
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]


def test_development_factory_registers_rate_limiting():
    app = create_app("development")

    assert app.config["RATELIMIT_ENABLED"] is True
    assert "limiter" in app.extensions


def test_environment_configuration_profiles_are_explicit():
    assert get_config("development") is DevelopmentConfig
    assert get_config("testing") is TestingConfig
    assert DevelopmentConfig.DEBUG is True
    assert DevelopmentConfig.RATELIMIT_ENABLED is True
    assert TestingConfig.TESTING is True
    assert TestingConfig.DEBUG is False
    assert TestingConfig.RATELIMIT_ENABLED is False
    assert ProductionConfig.DEBUG is False
    assert ProductionConfig.RATELIMIT_ENABLED is True
    assert ProductionConfig.SESSION_COOKIE_SECURE is True
    assert ProductionConfig.TALISMAN_FORCE_HTTPS is True


def test_production_configuration_rejects_unsafe_security_settings(monkeypatch):
    monkeypatch.setattr(ProductionConfig, "SECRET_KEY", "too-short")
    monkeypatch.setattr(ProductionConfig, "DB_PASSWORD", "dedicated-production-password")
    with pytest.raises(RuntimeError, match="Production SECRET_KEY"):
        ProductionConfig.validate()

    monkeypatch.setattr(ProductionConfig, "SECRET_KEY", "x" * 48)
    monkeypatch.setattr(
        ProductionConfig, "MFA_ENCRYPTION_KEY", Fernet.generate_key().decode("ascii")
    )
    monkeypatch.setattr(ProductionConfig, "RATELIMIT_STORAGE_URI", "memory://")
    with pytest.raises(RuntimeError, match="RATELIMIT_STORAGE_URI"):
        ProductionConfig.validate()
