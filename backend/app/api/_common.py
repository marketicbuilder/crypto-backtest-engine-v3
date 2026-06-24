"""Shared helpers used by API routers."""
from __future__ import annotations

import pandas as pd

from ..data.loader import load_dataset
from ..engine import BacktestConfig
from .schemas import BacktestRequest, DataRequest


def fetch_df(req: DataRequest) -> pd.DataFrame:
    return load_dataset(
        symbol=req.symbol, interval=req.interval,
        start=req.start, end=req.end, source=req.source,
        with_fear_greed=req.with_fear_greed, with_news=req.with_news,
    )


def to_config(req: BacktestRequest) -> BacktestConfig:
    return BacktestConfig(
        starting_balance=req.starting_balance,
        fee_pct=req.fee_pct,
        slippage_pct=req.slippage_pct,
        risk_per_trade=req.risk_per_trade,
        max_open_positions=req.max_open_positions,
        stop_loss_pct=req.stop_loss_pct,
        take_profit_pct=req.take_profit_pct,
        trailing_stop_pct=req.trailing_stop_pct,
        leverage=req.leverage,
        allow_short=req.allow_short,
    )
