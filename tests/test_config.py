import config


def test_get_drive_root_id_returns_value_from_secrets(monkeypatch):
    monkeypatch.setattr(config.st, "secrets", {"drive_roots": {"FDA": "abc123"}})
    assert config.get_drive_root_id("FDA") == "abc123"


def test_get_drive_root_id_returns_none_for_unmapped_client(monkeypatch):
    monkeypatch.setattr(config.st, "secrets", {"drive_roots": {"FDA": "abc123"}})
    assert config.get_drive_root_id("TH") is None


def test_get_default_subfolders_reads_from_secrets(monkeypatch):
    monkeypatch.setattr(config.st, "secrets", {"default_subfolders": ["Fotos", "Totales"]})
    assert config.get_default_subfolders() == ["Fotos", "Totales"]


def test_get_app_password_reads_from_secrets(monkeypatch):
    monkeypatch.setattr(config.st, "secrets", {"app_password": "clave123"})
    assert config.get_app_password() == "clave123"


def test_get_campaigns_api_url_reads_from_secrets(monkeypatch):
    monkeypatch.setattr(config.st, "secrets", {"campaigns_api_url": "https://example.com/allCampaigns"})
    assert config.get_campaigns_api_url() == "https://example.com/allCampaigns"
