"""Discord webhook alert adapter."""
from __future__ import annotations

import logging

import requests

from ..core import settings

log = logging.getLogger(__name__)


def send(text: str) -> bool:
    if not settings.discord_webhook_url:
        log.info("discord disabled (no webhook url) — would send: %s", text)
        return False
    r = requests.post(settings.discord_webhook_url, json={"content": text}, timeout=10)
    return r.ok
