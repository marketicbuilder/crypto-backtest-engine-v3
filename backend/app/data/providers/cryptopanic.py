"""CryptoPanic free news feed.

Returns posts with a coarse sentiment label derived from the
``votes`` block (positive - negative).
"""
from __future__ import annotations

from typing import Optional

import pandas as pd
import requests

from ...core import cache, settings


def fetch_posts(currencies: str = "BTC", days: int = 30) -> pd.DataFrame:
    cache_key = {"currencies": currencies, "days": days}
    cached = cache.get_df("cryptopanic.posts", cache_key, ttl=3 * 3600)
    if cached is not None:
        return cached

    if not settings.cryptopanic_token:
        # graceful degradation: return empty frame so the engine still runs
        return pd.DataFrame(columns=["time", "title", "sentiment"]).set_index("time")

    r = requests.get(
        f"{settings.cryptopanic_base}/posts/",
        params={"auth_token": settings.cryptopanic_token, "currencies": currencies,
                "kind": "news", "public": "true"},
        timeout=20,
    )
    r.raise_for_status()
    posts = r.json().get("results", [])
    rows = []
    for p in posts:
        v = p.get("votes", {}) or {}
        sent = (v.get("positive", 0) - v.get("negative", 0))
        rows.append({"time": p["published_at"], "title": p["title"], "sentiment": sent})
    df = pd.DataFrame(rows)
    if not df.empty:
        df["time"] = pd.to_datetime(df["time"], utc=True)
        df = df.set_index("time").sort_index()
    cache.set_df("cryptopanic.posts", cache_key, df)
    return df


def daily_sentiment(currencies: str = "BTC", days: int = 30) -> pd.Series:
    """Aggregate post sentiment to a daily mean in [-1, 1]."""
    posts = fetch_posts(currencies, days)
    if posts.empty:
        return pd.Series(dtype="float64", name="news_sent")
    s = posts["sentiment"].resample("1D").mean()
    s = s.clip(-5, 5) / 5.0
    s.name = "news_sent"
    return s
