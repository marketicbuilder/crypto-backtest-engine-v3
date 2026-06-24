"""Market-data endpoints (used by the frontend's symbol picker)."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Query

from ..data.loader import load_dataset
from ..data.providers import coingecko

router = APIRouter(prefix="/data", tags=["data"])


@router.get("/search")
def search(q: str = Query(..., min_length=1)) -> List[dict]:
    return coingecko.search_coin(q)[:20]


@router.get("/ohlcv")
def ohlcv(
    symbol: str = "BTCUSDT", interval: str = "1d",
    start: str | None = None, end: str | None = None,
    source: str = "binance",
) -> List[dict]:
    df = load_dataset(symbol=symbol, interval=interval, start=start, end=end,
                      source=source, with_fear_greed=False, with_news=False)
    return [
        {"t": str(t), "o": float(r.open), "h": float(r.high),
         "l": float(r.low), "c": float(r.close), "v": float(r.volume)}
        for t, r in df.iterrows()
    ]
