"""CoinGecko free-tier — market chart endpoint.

Returns daily OHLC + volume.  Used as a fallback when Binance is
geo-blocked or for non-Binance assets.
"""
from __future__ import annotations

from typing import Optional

import pandas as pd
import requests

from ...core import cache, settings


def fetch_market_chart(
    coin_id: str = "bitcoin",
    vs: str = "usd",
    days: int | str = 365,
) -> pd.DataFrame:
    cache_key = {"coin": coin_id, "vs": vs, "days": days}
    cached = cache.get_df("coingecko.chart", cache_key)
    if cached is not None:
        return cached

    r = requests.get(
        f"{settings.coingecko_base}/coins/{coin_id}/market_chart",
        params={"vs_currency": vs, "days": days, "interval": "daily"},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    prices = pd.DataFrame(data["prices"], columns=["ts", "price"])
    volumes = pd.DataFrame(data["total_volumes"], columns=["ts", "volume"])
    df = prices.merge(volumes, on="ts")
    df["time"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    df["close"] = df["price"]
    df["open"] = df["close"].shift(1).fillna(df["close"])
    df["high"] = df[["open", "close"]].max(axis=1)
    df["low"] = df[["open", "close"]].min(axis=1)
    df = df.set_index("time")[["open", "high", "low", "close", "volume"]]
    cache.set_df("coingecko.chart", cache_key, df)
    return df


def search_coin(query: str) -> list[dict]:
    r = requests.get(f"{settings.coingecko_base}/search", params={"query": query}, timeout=15)
    r.raise_for_status()
    return r.json().get("coins", [])
