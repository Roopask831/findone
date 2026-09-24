from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import config, db
from app.config import Settings


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    settings = Settings(findone_key="test-key")
    settings.data_dir = tmp_path / "data"
    settings.data_dir.mkdir()
    config.get_settings.cache_clear()
    monkeypatch.setattr(config, "get_settings", lambda: settings)
    db.reset_engine()
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client, settings
    db.reset_engine()
