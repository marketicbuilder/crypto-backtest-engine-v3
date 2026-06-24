"""Unified alerts entry-point used by both backtest and live runners."""
from __future__ import annotations

from typing import Iterable

from . import discord, telegram


def broadcast(text: str, channels: Iterable[str] = ("telegram", "discord")) -> dict:
    out = {}
    if "telegram" in channels:
        out["telegram"] = telegram.send(text)
    if "discord" in channels:
        out["discord"] = discord.send(text)
    return out


__all__ = ["broadcast", "telegram", "discord"]
