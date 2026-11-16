import pytest
from fastapi import HTTPException

from config import settings
from security import require_api_key


def test_api_key_disabled_allows_request(monkeypatch):
    monkeypatch.setattr(settings, "API_REQUIRE_KEY", False)

    assert require_api_key(None) is None


def test_api_key_required_rejects_missing_key(monkeypatch):
    monkeypatch.setattr(settings, "API_REQUIRE_KEY", True)
    monkeypatch.setattr(settings, "API_KEY", "secret")

    with pytest.raises(HTTPException) as exc:
        require_api_key(None)

    assert exc.value.status_code == 401


def test_api_key_required_accepts_matching_key(monkeypatch):
    monkeypatch.setattr(settings, "API_REQUIRE_KEY", True)
    monkeypatch.setattr(settings, "API_KEY", "secret")

    assert require_api_key("secret") is None
