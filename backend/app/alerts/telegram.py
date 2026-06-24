"""Telegram alert adapter — used by future live-trading mode."""
from __future__ import annotations

import logging

import requests

from ..core import settings

log = logging.getLogger(__name__)


def send(text: str, *, parse_mode: str = "Markdown") -> bool:
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        log.info("telegram disabled (no token / chat id) — would send: %s", text)
        return False
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    r = requests.post(url, json={
        "chat_id": settings.telegram_chat_id, "text": text, "parse_mode": parse_mode,
    }, timeout=10)
    return r.ok
