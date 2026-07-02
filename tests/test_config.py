from app.core.config import Settings


def test_default_settings_are_safe():
    settings = Settings(_env_file=None)
    assert settings.enable_live_trading is False
    assert settings.max_position_risk_pct <= 5


def test_live_trading_is_blocked():
    settings = Settings(_env_file=None, enable_live_trading=True)
    try:
        settings.validate_safety()
    except ValueError as exc:
        assert "not allowed" in str(exc)
    else:
        raise AssertionError("Live trading should be blocked in Volume 1")
