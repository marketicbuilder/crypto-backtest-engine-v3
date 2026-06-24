"""End-to-end demo runner.

Loads 5y BTC/USDT daily data → backtests the three bundled strategies →
optimises the EMA-cross parameters → writes:

    output/demo/metrics.json
    output/demo/trades.csv
    output/demo/equity.csv
    output/demo/report.html

Run from the repo root:  ``python -m backend.scripts.run_demo``
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd

from app.data.loader import load_csv
from app.engine import BacktestConfig, BacktestEngine
from app.insights import generate_insights
from app.optimization import grid_search, sharpe_objective
from app.strategies import get_strategy, list_strategies


DEMO_OUT = Path(os.environ.get("DEMO_OUT", "output/demo"))
DATA_FILE = Path(os.environ.get("DATA_FILE", "data/btcusdt_1d.csv"))


def _format_metrics(m: dict) -> dict:
    """Strip non-JSON-safe values from a metrics dict."""
    return {k: (None if isinstance(v, pd.Series) else v)
            for k, v in m.items() if k != "drawdown_series"}


def main() -> None:
    DEMO_OUT.mkdir(parents=True, exist_ok=True)
    df = load_csv(str(DATA_FILE))
    print(f"loaded {len(df)} bars from {df.index.min().date()} → {df.index.max().date()}")

    base_cfg = BacktestConfig(
        starting_balance=10_000,
        fee_pct=0.001,
        slippage_pct=0.0005,
        risk_per_trade=0.02,
        stop_loss_pct=0.08,
        take_profit_pct=0.25,
        trailing_stop_pct=0.10,
        leverage=1.0,
    )

    # 1) backtest every bundled strategy
    summary: dict = {"strategies": {}}
    for name in list_strategies():
        strat = get_strategy(name)
        res = BacktestEngine(base_cfg).run(df, strat)
        summary["strategies"][name] = _format_metrics(res.metrics)
        print(f"  {name:14s} return={res.metrics['total_return']*100:7.2f}%  "
              f"sharpe={res.metrics['sharpe_ratio']:5.2f}  "
              f"mdd={res.metrics['max_drawdown']*100:7.2f}%  "
              f"trades={res.metrics['total_trades']}")

    # 2) optimise ema_cross
    print("optimising ema_cross …")
    report = grid_search(
        df, "ema_cross",
        {"fast": [9, 12, 20, 30], "slow": [26, 50, 100, 200]},
        base_cfg, sharpe_objective,
    )
    summary["optimisation"] = {
        "best_params": report.best_params,
        "top5": report.table.head().to_dict(orient="records"),
    }

    # 3) run the best config end-to-end, save artefacts
    best = report.best_result
    summary["best"] = _format_metrics(best.metrics)
    summary["best"]["strategy"] = "ema_cross"
    summary["best"]["params"] = report.best_params
    summary["best"]["insights"] = generate_insights(best, df["close"])
    summary["benchmark"] = {
        "buy_and_hold_return": float(df["close"].iloc[-1] / df["close"].iloc[0] - 1),
        "asset": "BTCUSDT",
        "start": str(df.index.min().date()),
        "end": str(df.index.max().date()),
        "bars": len(df),
    }

    # 4) write artefacts
    (DEMO_OUT / "metrics.json").write_text(json.dumps(summary, indent=2, default=str))
    pd.DataFrame([t.to_dict() for t in best.trades]).to_csv(DEMO_OUT / "trades.csv", index=False)
    best.equity.to_csv(DEMO_OUT / "equity.csv", header=["equity"])
    best.signals.to_csv(DEMO_OUT / "signals.csv")
    print(f"\nwrote {DEMO_OUT}/{{metrics.json,trades.csv,equity.csv,signals.csv}}")


if __name__ == "__main__":
    main()
