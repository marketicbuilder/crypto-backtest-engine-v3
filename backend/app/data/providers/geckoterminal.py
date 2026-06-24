"""GeckoTerminal DEX data — used for on-chain price discovery on long-tail tokens."""
from __future__ import annotations

import pandas as pd
import requests

from ...core import cache, settings


def pool_ohlcv(network: str, pool: str, timeframe: str = "day", aggregate: int = 1,
               limit: int = 365) -> pd.DataFrame:
    cache_key = {"network": network, "pool": pool, "tf": timeframe, "agg": aggregate, "limit": limit}
    cached = cache.get_df("gecko.pool_ohlcv", cache_key)
    if cached is not None:
        return cached
    url = f"{settings.geckoterminal_base}/networks/{network}/pools/{pool}/ohlcv/{timeframe}"
    r = requests.get(url, params={"aggregate": aggregate, "limit": limit}, timeout=30)
    r.raise_for_status()
    rows = (r.json().get("data", {}) or {}).get("attributes", {}).get("ohlcv_list", [])
    df = pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume"]).astype(float)
    df["time"] = pd.to_datetime(df["ts"].astype("int64"), unit="s", utc=True)
    df = df.set_index("time")[["open", "high", "low", "close", "volume"]].sort_index()
    cache.set_df("gecko.pool_ohlcv", cache_key, df)
    return df
