"""DefiLlama free API — TVL by chain or protocol (on-chain context)."""
from __future__ import annotations

import pandas as pd
import requests

from ...core import cache, settings


def chain_tvl(chain: str = "ethereum") -> pd.Series:
    cache_key = {"chain": chain}
    cached = cache.get_df("defillama.chain_tvl", cache_key, ttl=6 * 3600)
    if cached is not None:
        return cached["tvl"]
    r = requests.get(f"{settings.defillama_base}/v2/historicalChainTvl/{chain}", timeout=30)
    r.raise_for_status()
    rows = r.json()
    df = pd.DataFrame(rows)
    df["time"] = pd.to_datetime(df["date"].astype("int64"), unit="s", utc=True)
    df = df.set_index("time")[["tvl"]].astype(float).sort_index()
    cache.set_df("defillama.chain_tvl", cache_key, df)
    return df["tvl"]
