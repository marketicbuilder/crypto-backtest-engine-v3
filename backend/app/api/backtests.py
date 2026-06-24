"""Backtest endpoints."""
from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd
from fastapi import APIRouter, HTTPException

from ..engine import BacktestEngine
from ..insights import generate_insights
from ..optimization import (calmar_objective, grid_search,
                            sharpe_objective, total_return_objective)
from ..strategies import get_strategy
from . import _common
from .schemas import (BacktestRequest, BacktestResponse, CompareRequest,
                      OptimiseRequest, TradeOut)

router = APIRouter(prefix="/backtests", tags=["backtests"])


def _serialise_metrics(m: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in m.items() if not isinstance(v, pd.Series)}


@router.post("/run", response_model=BacktestResponse)
def run_backtest(req: BacktestRequest) -> BacktestResponse:
    try:
        df = _common.fetch_df(req.data)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(502, f"data fetch failed: {e}")
    try:
        strat = get_strategy(req.strategy.name, **req.strategy.params)
    except KeyError as e:
        raise HTTPException(404, str(e))
    cfg = _common.to_config(req)
    result = BacktestEngine(cfg).run(df, strat)
    eq = [{"t": str(t), "v": float(v)} for t, v in result.equity.items()]
    dd_series = result.metrics["drawdown_series"]
    dd = [{"t": str(t), "v": float(v) * 100} for t, v in dd_series.items()]
    return BacktestResponse(
        metrics=_serialise_metrics(result.metrics),
        trades=[TradeOut(**t.to_dict()) for t in result.trades],
        equity=eq,
        drawdown=dd,
        insights=generate_insights(result, df["close"]),
        strategy=req.strategy,
    )


@router.post("/compare")
def compare(req: CompareRequest) -> List[Dict]:
    df = _common.fetch_df(req.data)
    out = []
    cfg = _common.to_config(BacktestRequest(data=req.data,
                                            strategy=req.strategies[0],
                                            starting_balance=req.starting_balance))
    for spec in req.strategies:
        strat = get_strategy(spec.name, **spec.params)
        res = BacktestEngine(cfg).run(df, strat)
        m = _serialise_metrics(res.metrics)
        out.append({"strategy": spec.model_dump(), "metrics": m,
                    "trades": len(res.trades)})
    return out


@router.post("/optimise")
def optimise(req: OptimiseRequest) -> Dict:
    df = _common.fetch_df(req.data)
    cfg = _common.to_config(BacktestRequest(
        data=req.data, strategy={"name": req.strategy_name},
        starting_balance=req.starting_balance, fee_pct=req.fee_pct,
        slippage_pct=req.slippage_pct,
    ))
    obj = {"sharpe": sharpe_objective, "calmar": calmar_objective,
           "return": total_return_objective}.get(req.objective)
    if obj is None:
        raise HTTPException(400, f"unknown objective {req.objective!r}")
    report = grid_search(df, req.strategy_name, req.param_grid, cfg, obj)
    return {
        "best_params": report.best_params,
        "best_metrics": _serialise_metrics(report.best_result.metrics),
        "table": report.table.to_dict(orient="records"),
    }
