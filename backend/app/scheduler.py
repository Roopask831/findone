"""Work-window clock helpers. Discovery polling arrives in a later phase."""

from __future__ import annotations

from datetime import datetime, timedelta

from app.config import load_profile, operations_allowed, parse_hhmm

__all__ = ["next_poll_at", "operations_allowed"]


def next_poll_at(now: datetime | None = None, profile: dict | None = None) -> datetime:
    """Next discovery tick: every poll_minutes, aligned to work_start when the clock is on."""
    profile = profile if profile is not None else load_profile()
    current = now or datetime.now().astimezone()
    poll = int(profile.get("poll_minutes", 20))
    start = parse_hhmm(profile.get("work_start", "06:00"))
    end = parse_hhmm(profile.get("work_end", "15:30"))
    enforce = bool(profile.get("enforce_work_window", False))

    def combine(day: datetime, clock) -> datetime:
        return datetime.combine(day.date(), clock, tzinfo=current.tzinfo)

    if not enforce:
        return current + timedelta(minutes=poll)

    start_today = combine(current, start)
    end_today = combine(current, end)
    if current < start_today:
        return start_today
    if current >= end_today:
        return start_today + timedelta(days=1)

    elapsed_minutes = (current - start_today).total_seconds() / 60
    slots = int(elapsed_minutes // poll) + 1
    candidate = start_today + timedelta(minutes=slots * poll)
    if candidate > end_today:
        return start_today + timedelta(days=1)
    return candidate
