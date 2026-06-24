"""Insights endpoint — accepts an already-run backtest payload and
returns rule-based insights (useful when the frontend caches results)."""
from __future__ import annotations

from typing import List

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..insights import generate_insights
from ..engine import BacktestResult, BacktestConfig

router = APIRouter(prefix="/insights", tags=["insights"])


class InsightsIn(BaseModel):
    equity: list[dict]
    trades: list[dict]
    prices: list[dict]
    config: dict | None = None


@router.post("")
def insights(req: InsightsIn) -> List[str]:
    try:
        eq = pd.Series(
            [p["v"] for p in req.equity],
            index=pd.DatetimeIndex([pd.Timestamp(p["t"]) for p in req.equity]),
        )
        prices = pd.Series(
            [p["c"] for p in req.prices],
            index=pd.DatetimeIndex([pd.Timestamp(p["t"]) for p in req.prices]),
        )
        from ..engine.metrics import Trade, compute_metrics
        trades = [Trade(
            entry_time=pd.Timestamp(t["entry_time"]),
            exit_time=pd.Timestamp(t["exit_time"]),
            side=t["side"], entry_price=float(t["entry_price"]),
            exit_price=float(t["exit_price"]), qty=float(t["qty"]),
            pnl=float(t["pnl"]), pnl_pct=float(t["pnl_pct"]),
            fees=float(t.get("fees", 0)), score=float(t.get("score", 0)),
            reason_entry=t.get("reason_entry", ""), reason_exit=t.get("reason_exit", ""),
        ) for t in req.trades]
        metrics = compute_metrics(eq, trades, eq.iloc[0])
        cfg = BacktestConfig(**(req.config or {}))
        res = BacktestResult(equity=eq, trades=trades, metrics=metrics,
                             signals=pd.DataFrame(), config=cfg)
        return generate_insights(res, prices)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(400, f"could not build insights: {e}")
