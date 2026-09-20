"""Local API key check for mutating routes."""

from __future__ import annotations

from fastapi import Header, HTTPException, status

from app import config


def require_api_key(x_findone_key: str | None = Header(default=None, alias="X-FindOne-Key")) -> None:
    expected = config.get_settings().findone_key
    if not x_findone_key or x_findone_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid X-FindOne-Key",
        )
