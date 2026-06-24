"""Bitget public-market candles.

Free, no auth.  ``granularity`` follows Bitget convention (e.g. ``1D``).
"""
from __future__ import annotations

from typing import Optional

import pandas as pd
import requests

from ...core import cache, settings


def fetch_ohlcv(
    symbol: str = "BTCUSDT",
    granularity: str = "1D",
    limit: int = 1000,
) -> pd.DataFrame:
    cache_key = {"symbol": symbol, "granularity": granularity, "limit": limit}
    cached = cache.get_df("bitget.candles", cache_key)
    if cached is not None:
        return cached
    r = requests.get(
        f"{settings.bitget_base}/api/v2/spot/market/candles",
        params={"symbol": symbol, "granularity": granularity, "limit": limit},
        timeout=20,
    )
    r.raise_for_status()
    rows = r.json().get("data", [])
    df = pd.DataFrame(rows, columns=[
        "ts", "open", "high", "low", "close", "base_vol", "quote_vol", "usdt_vol",
    ]).astype({"open": "float", "high": "float", "low": "float",
               "close": "float", "base_vol": "float"})
    df["time"] = pd.to_datetime(df["ts"].astype("int64"), unit="ms", utc=True)
    df["volume"] = df["base_vol"]
    df = df.set_index("time")[["open", "high", "low", "close", "volume"]].sort_index()
    cache.set_df("bitget.candles", cache_key, df)
    return df
