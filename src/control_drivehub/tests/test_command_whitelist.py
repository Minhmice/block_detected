from pi_monitor.core.commands import validate_command
from pi_monitor.core.config import CommandsConfig
from pi_monitor.core.schema import CommandRequest


def test_reject_when_disabled():
    cfg = CommandsConfig(enabled=False, token="secret")
    req = CommandRequest(type="emergency_stop", token="secret")
    result = validate_command(cfg, req)
    assert not result.ok


def test_reject_bad_token():
    cfg = CommandsConfig(enabled=True, token="secret")
    req = CommandRequest(type="emergency_stop", token="wrong")
    result = validate_command(cfg, req)
    assert not result.ok


def test_reject_not_whitelisted():
    cfg = CommandsConfig(enabled=True, token="secret", whitelist=["emergency_stop"])
    req = CommandRequest(type="set_motor_power", token="secret")
    result = validate_command(cfg, req)
    assert not result.ok


def test_accept_emergency_stop():
    cfg = CommandsConfig(enabled=True, token="secret", whitelist=["emergency_stop"])
    req = CommandRequest(type="emergency_stop", token="secret")
    result = validate_command(cfg, req)
    assert result.ok
