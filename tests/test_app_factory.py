import pytest
from cryptography.fernet import Fernet

from app import create_app
from app.extensions import csrf, limiter, login_manager, talisman
from config import DevelopmentConfig, ProductionConfig, TestingConfig, get_config


def test_extensions_are_singletons_outside_the_model_package():
    from app import extensions

    assert extensions.limiter is limiter


def test_testing_factory_initializes_security_extensions():
    app = create_app("testing")

    assert app.testing is True
    assert app.debug is False
    assert app.login_manager is login_manager
    assert app.extensions["csrf"] is csrf
    assert "limiter" in app.extensions

    response = app.test_client().get("/api/ping")
    assert response.status_code == 200
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]


def test_environment_configuration_profiles_are_explicit():
    assert get_config("development") is DevelopmentConfig
    assert get_config("testing") is TestingConfig
    assert DevelopmentConfig.DEBUG is True
    assert TestingConfig.TESTING is True
    assert TestingConfig.DEBUG is False
    assert ProductionConfig.DEBUG is False
    assert ProductionConfig.SESSION_COOKIE_SECURE is True
    assert ProductionConfig.TALISMAN_FORCE_HTTPS is True


def test_production_configuration_rejects_weak_secret(monkeypatch):
    monkeypatch.setattr(ProductionConfig, "SECRET_KEY", "too-short")
    monkeypatch.setattr(ProductionConfig, "DB_PASSWORD", "dedicated-production-password")

    with pytest.raises(RuntimeError, match="Production SECRET_KEY"):
        ProductionConfig.validate()


def test_production_configuration_requires_external_security_services(monkeypatch):
    monkeypatch.setattr(ProductionConfig, "SECRET_KEY", "x" * 48)
    monkeypatch.setattr(ProductionConfig, "DB_PASSWORD", "dedicated-production-password")
    monkeypatch.setattr(
        ProductionConfig, "MFA_ENCRYPTION_KEY", Fernet.generate_key().decode("ascii")
    )
    monkeypatch.setattr(ProductionConfig, "RATELIMIT_STORAGE_URI", "memory://")

    with pytest.raises(RuntimeError, match="RATELIMIT_STORAGE_URI"):
        ProductionConfig.validate()


def test_unknown_environment_is_rejected():
    with pytest.raises(RuntimeError, match="Unknown APP_ENV"):
        get_config("unknown")


def test_talisman_is_instantiated_once():
    assert talisman is not None
