"""Runtime configuration loaded from environment variables.

Free-tier defaults — set the matching environment variable to override.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    binance_base: str = os.environ.get("BINANCE_BASE", "https://api.binance.com")
    bitget_base: str = os.environ.get("BITGET_BASE", "https://api.bitget.com")
    coingecko_base: str = os.environ.get("COINGECKO_BASE", "https://api.coingecko.com/api/v3")
    cryptopanic_base: str = os.environ.get("CRYPTOPANIC_BASE", "https://cryptopanic.com/api/v1")
    cryptopanic_token: str = os.environ.get("CRYPTOPANIC_TOKEN", "")
    alternative_me_base: str = os.environ.get("ALT_ME_BASE", "https://api.alternative.me")
    defillama_base: str = os.environ.get("DEFILLAMA_BASE", "https://api.llama.fi")
    geckoterminal_base: str = os.environ.get("GECKOTERMINAL_BASE", "https://api.geckoterminal.com/api/v2")

    supabase_url: str = os.environ.get("SUPABASE_URL", "")
    supabase_key: str = os.environ.get("SUPABASE_SERVICE_KEY", "")
    cache_dir: str = os.environ.get("CACHE_DIR", ".cache")

    telegram_bot_token: str = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.environ.get("TELEGRAM_CHAT_ID", "")
    discord_webhook_url: str = os.environ.get("DISCORD_WEBHOOK_URL", "")


settings = Settings()
