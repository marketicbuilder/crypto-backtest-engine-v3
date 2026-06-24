"""Binance public REST — historical klines.

Free, no API key required.  Klines endpoint returns at most 1000 bars
per call so we page automatically.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Optional

import pandas as pd
import requests

from ...core import cache, settings

_INTERVAL_MS = {
    "1m": 60_000, "5m": 300_000, "15m": 900_000, "30m": 1_800_000,
    "1h": 3_600_000, "4h": 14_400_000, "1d": 86_400_000, "1w": 604_800_000,
}


def fetch_ohlcv(
    symbol: str = "BTCUSDT",
    interval: str = "1d",
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> pd.DataFrame:
    """Return OHLCV DataFrame indexed by UTC timestamp.

    ``start`` / ``end`` are ISO date strings (YYYY-MM-DD) or None.
    """
    if interval not in _INTERVAL_MS:
        raise ValueError(f"unsupported interval {interval!r}")

    cache_key = {"symbol": symbol, "interval": interval, "start": start, "end": end}
    cached = cache.get_df("binance.klines", cache_key)
    if cached is not None:
        return cached

    end_ms = int(datetime.now(timezone.utc).timestamp() * 1000) if end is None \
        else int(pd.Timestamp(end, tz="UTC").timestamp() * 1000)
    start_ms = end_ms - 365 * 5 * 86_400_000 if start is None \
        else int(pd.Timestamp(start, tz="UTC").timestamp() * 1000)

    rows: list[list] = []
    cur = start_ms
    step = _INTERVAL_MS[interval]
    while cur < end_ms:
        resp = requests.get(
            f"{settings.binance_base}/api/v3/klines",
            params={
                "symbol": symbol, "interval": interval,
                "startTime": cur, "endTime": end_ms, "limit": 1000,
            }, timeout=20,
        )
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        rows.extend(batch)
        cur = batch[-1][0] + step
        time.sleep(0.05)  # gentle on rate limits

    df = pd.DataFrame(rows, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "qav", "trades", "tbav", "tqav", "ignore",
    ])
    df = df[["open_time", "open", "high", "low", "close", "volume"]].astype({
        "open": "float", "high": "float", "low": "float",
        "close": "float", "volume": "float",
    })
    df["time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df = df.drop(columns=["open_time"]).set_index("time")
    cache.set_df("binance.klines", cache_key, df)
    return df
