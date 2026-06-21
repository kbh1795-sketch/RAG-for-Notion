from __future__ import annotations

from datetime import datetime, timezone
from math import exp
from typing import Mapping, Optional

DEFAULT_HALF_LIFE_DAYS = 30.0


def parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    value = value.strip()
    if value.endswith('Z'):
        value = value[:-1] + '+00:00'
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def recency_weight(last_edited_time: Optional[str] = None, created_time: Optional[str] = None, *, now: Optional[datetime] = None, half_life_days: float = DEFAULT_HALF_LIFE_DAYS) -> float:
    if half_life_days <= 0:
        raise ValueError('half_life_days must be greater than 0')
    timestamp = parse_datetime(last_edited_time) or parse_datetime(created_time)
    if timestamp is None:
        return 0.0
    reference = now or datetime.now(timezone.utc)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=timezone.utc)
    age_days = max((reference.astimezone(timezone.utc) - timestamp).total_seconds(), 0.0) / 86400.0
    return exp(-age_days / half_life_days)


def document_recency_weight(document: Mapping[str, object], *, now: Optional[datetime] = None, half_life_days: float = DEFAULT_HALF_LIFE_DAYS) -> float:
    return recency_weight(str(document.get('last_edited_time', '')), str(document.get('created_time', '')), now=now, half_life_days=half_life_days)
