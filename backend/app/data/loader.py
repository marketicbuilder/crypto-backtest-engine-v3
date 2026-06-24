"""Unified loader that joins price + Fear&Greed + news sentiment.

Falls back gracefully when an optional source is unavailable so the
engine still works with just OHLCV.
"""
from __future__ import annotations

from typing import Optional

import pandas as pd

from .providers import alternative_me, binance, coingecko, cryptopanic


def load_dataset(
    symbol: str = "BTCUSDT",
    interval: str = "1d",
    start: Optional[str] = None,
    end: Optional[str] = None,
    *,
    source: str = "binance",
    with_fear_greed: bool = True,
    with_news: bool = False,
    news_currency: str = "BTC",
) -> pd.DataFrame:
    if source == "binance":
        px = binance.fetch_ohlcv(symbol, interval, start, end)
    elif source == "coingecko":
        days = "max" if start is None else (pd.Timestamp.utcnow() - pd.Timestamp(start, tz="UTC")).days
        px = coingecko.fetch_market_chart(symbol.lower(), days=days)
    else:
        raise ValueError(f"unknown source {source!r}")

    out = px.copy()
    if with_fear_greed:
        fg = alternative_me.fetch_fear_greed()
        if not fg.empty:
            fg.index = fg.index.tz_convert("UTC") if fg.index.tz else fg.index.tz_localize("UTC")
            out = out.join(fg.reindex(out.index, method="nearest"), how="left")
    if with_news:
        ns = cryptopanic.daily_sentiment(news_currency)
        if not ns.empty:
            out = out.join(ns.reindex(out.index, method="nearest"), how="left")
    return out


def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["time"] = pd.to_datetime(df["time"], utc=True)
    df = df.set_index("time").sort_index()
    for c in ("open", "high", "low", "close", "volume"):
        df[c] = df[c].astype(float)
    return df
