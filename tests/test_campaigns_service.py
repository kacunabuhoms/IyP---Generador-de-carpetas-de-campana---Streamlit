import pandas as pd
import pytest

import campaigns_service
import config


class _StubResponse:
    def __init__(self, json_data, status_code=200):
        self._json_data = json_data
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise campaigns_service.requests.HTTPError(f"status {self.status_code}")

    def json(self):
        return self._json_data


def test_get_campaigns_returns_dataframe_from_api(monkeypatch):
    monkeypatch.setattr(config.st, "secrets", {"campaigns_api_url": "https://example.com/allCampaigns"})
    payload = {
        "ok": True,
        "campanas": [
            {
                "campaign_id": 212,
                "campana": "FDA SALUD VISUAL26",
                "cliente": "FDA",
                "fecha_inicio": None,
                "fecha_fin": None,
            },
        ],
    }

    def fake_get(url, headers=None, timeout=None):
        assert url == "https://example.com/allCampaigns"
        return _StubResponse(payload)

    monkeypatch.setattr(campaigns_service.requests, "get", fake_get)

    df = campaigns_service.get_campaigns()

    assert isinstance(df, pd.DataFrame)
    assert df.iloc[0]["cliente"] == "FDA"
    assert df.iloc[0]["campana"] == "FDA SALUD VISUAL26"


def test_get_campaigns_uses_20_second_timeout(monkeypatch):
    monkeypatch.setattr(config.st, "secrets", {"campaigns_api_url": "https://example.com/allCampaigns"})
    captured = {}

    def fake_get(url, headers=None, timeout=None):
        captured["timeout"] = timeout
        return _StubResponse({"ok": True, "campanas": []})

    monkeypatch.setattr(campaigns_service.requests, "get", fake_get)

    campaigns_service.get_campaigns()

    assert captured["timeout"] == 20


def test_get_campaigns_raises_when_api_reports_not_ok(monkeypatch):
    monkeypatch.setattr(config.st, "secrets", {"campaigns_api_url": "https://example.com/allCampaigns"})

    def fake_get(url, headers=None, timeout=None):
        return _StubResponse({"ok": False, "campanas": []})

    monkeypatch.setattr(campaigns_service.requests, "get", fake_get)

    with pytest.raises(RuntimeError):
        campaigns_service.get_campaigns()
