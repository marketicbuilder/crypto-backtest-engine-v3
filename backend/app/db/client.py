"""Tiny Supabase REST wrapper.

We avoid the heavy ``supabase-py`` dependency: a few JSON calls cover
what the API needs (insert/select). When ``SUPABASE_URL`` is empty the
client is a no-op so the engine works offline.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Optional

import requests

from ..core import settings

log = logging.getLogger(__name__)


class Supabase:
    def __init__(self) -> None:
        self.enabled = bool(settings.supabase_url and settings.supabase_key)
        self.base = settings.supabase_url.rstrip("/") + "/rest/v1" if self.enabled else ""
        self.headers = {
            "apikey": settings.supabase_key,
            "Authorization": f"Bearer {settings.supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        } if self.enabled else {}

    def insert(self, table: str, row: dict) -> Optional[dict]:
        if not self.enabled:
            log.debug("supabase disabled, skipping insert into %s", table)
            return None
        r = requests.post(f"{self.base}/{table}", headers=self.headers,
                          data=json.dumps(row, default=str), timeout=15)
        r.raise_for_status()
        data = r.json()
        return data[0] if data else None

    def select(self, table: str, *, filters: dict | None = None,
               limit: int = 100) -> list[dict]:
        if not self.enabled:
            return []
        params = {"limit": limit}
        for k, v in (filters or {}).items():
            params[k] = v
        r = requests.get(f"{self.base}/{table}", headers=self.headers,
                         params=params, timeout=15)
        r.raise_for_status()
        return r.json()


supabase = Supabase()
