import os


def test_generate_secret_key_length():
    from core.config.validation import generate_secret_key

    secret = generate_secret_key()
    assert isinstance(secret, str)
    assert len(secret) == 64


def test_validate_config_dev_returns_false_when_missing_required_secrets(monkeypatch):
    # In development mode, validator returns False (not strict) rather than raising
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.delenv("JWT_SECRET", raising=False)
    monkeypatch.delenv("APP_MEDIA_KEY", raising=False)

    from core.config.validation import validate_config

    assert validate_config(strict=False) is False


def test_validate_config_strict_raises_when_missing_required_secrets(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("JWT_SECRET", raising=False)
    monkeypatch.delenv("APP_MEDIA_KEY", raising=False)

    from core.config.validation import validate_config
    from core.config.validation import ConfigurationError

    raised = False
    try:
        validate_config(strict=True)
    except ConfigurationError:
        raised = True

    assert raised is True
