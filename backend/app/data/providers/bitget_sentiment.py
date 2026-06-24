"""Bitget public futures sentiment data — no auth required.

Fetches long/short ratio, funding rate and open interest from
Bitget's free public futures API and returns scalar values for
the current bar so the AI scoring engine can use them as signals.
"""
from __future__ import annotations

import requests

BASE = "https://api.bitget.com"


def fetch_long_short_ratio(symbol: str = "BTCUSDT", period: str = "1D") -> float:
    """Return latest long/short ratio. >1 = longs dominating, <1 = shorts."""
    try:
        r = requests.get(
            f"{BASE}/api/v2/mix/market/account-long-short-ratio",
            params={"symbol": symbol, "productType": "USDT-FUTURES", "period": period, "limit": 1},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json().get("data", [])
        if data:
            return float(data[0].get("longShortRatio", 1.0))
    except Exception:
        pass
    return 1.0  # neutral fallback


def fetch_funding_rate(symbol: str = "BTCUSDT") -> float:
    """Return current funding rate. Positive = longs pay shorts (overleveraged bulls)."""
    try:
        r = requests.get(
            f"{BASE}/api/v2/mix/market/current-fund-rate",
            params={"symbol": symbol, "productType": "USDT-FUTURES"},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json().get("data", [])
        if data:
            return float(data[0].get("fundingRate", 0.0))
    except Exception:
        pass
    return 0.0  # neutral fallback


def fetch_open_interest(symbol: str = "BTCUSDT") -> float:
    """Return current open interest in USD."""
    try:
        r = requests.get(
            f"{BASE}/api/v2/mix/market/open-interest",
            params={"symbol": symbol, "productType": "USDT-FUTURES"},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json().get("data", {})
        return float(data.get("openInterestValue", 0.0))
    except Exception:
        pass
    return 0.0
