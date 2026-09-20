"""Paths, env, and profile.yml settings."""

from __future__ import annotations

from datetime import datetime, time
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BACKEND_DIR.parent
PROFILE_PATH = Path(__file__).resolve().parent / "profile" / "profile.yml"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    findone_key: str = "change-me-local"
    aggregator_api_key: str = ""
    database_url: str = ""
    findone_host: str = "127.0.0.1"
    findone_port: int = 8000
    data_dir: Path = ROOT_DIR / "data"

    def sqlite_url(self) -> str:
        if self.database_url:
            return self.database_url
        db_path = (self.data_dir / "findone.db").resolve()
        return f"sqlite:///{db_path.as_posix()}"


def load_profile() -> dict:
    with PROFILE_PATH.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def parse_hhmm(value: str) -> time:
    hour, minute = value.split(":")
    return time(int(hour), int(minute))


def local_zone() -> ZoneInfo:
    return datetime.now().astimezone().tzinfo or ZoneInfo("America/New_York")


def clock_in_work_window(now: datetime | None = None, profile: dict | None = None) -> bool:
    """True only if local time is between work_start and work_end."""
    profile = profile if profile is not None else load_profile()
    current = now or datetime.now().astimezone()
    start = parse_hhmm(profile.get("work_start", "06:00"))
    end = parse_hhmm(profile.get("work_end", "15:30"))
    return start <= current.time() <= end


def operations_allowed(now: datetime | None = None, profile: dict | None = None) -> bool:
    """Hunt/apply/status 'running' gate. Clock is ignored until enforce_work_window is true."""
    profile = profile if profile is not None else load_profile()
    if not profile.get("enforce_work_window", False):
        return True
    return clock_in_work_window(now, profile)


def in_work_window(now: datetime | None = None, profile: dict | None = None) -> bool:
    """Used by later phases. Same as operations_allowed."""
    return operations_allowed(now, profile)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    (settings.data_dir / "resumes").mkdir(parents=True, exist_ok=True)
    return settings
