"""Alternative.me Crypto Fear & Greed index — free, no auth."""
from __future__ import annotations

import pandas as pd
import requests

from ...core import cache, settings


def fetch_fear_greed(limit: int = 0) -> pd.Series:
    cache_key = {"limit": limit}
    cached = cache.get_df("altme.fng", cache_key, ttl=12 * 3600)
    if cached is not None:
        return cached["value"]
    r = requests.get(f"{settings.alternative_me_base}/fng/",
                     params={"limit": limit, "format": "json"}, timeout=20)
    r.raise_for_status()
    rows = r.json().get("data", [])
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.Series(dtype="float64", name="fear_greed")
    df["time"] = pd.to_datetime(df["timestamp"].astype("int64"), unit="s", utc=True)
    df["value"] = df["value"].astype(float)
    df = df.set_index("time").sort_index()[["value"]]
    cache.set_df("altme.fng", cache_key, df)
    return df["value"].rename("fear_greed")
