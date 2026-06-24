"""Rule-based insights generator.

Reads the result of a backtest and produces human-readable suggestions.
No paid LLM is required — these are deterministic heuristics that the
quant team can review and extend.
"""
from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

from ..engine import BacktestResult


def _classify_regime(prices: pd.Series) -> pd.Series:
    """Tag each bar as bullish / bearish / sideways using a 50-bar slope."""
    slope = prices.pct_change(50)
    regime = pd.Series("sideways", index=prices.index)
    regime[slope > 0.05] = "bullish"
    regime[slope < -0.05] = "bearish"
    return regime


def generate_insights(result: BacktestResult, price_series: pd.Series) -> List[str]:
    out: List[str] = []
    m = result.metrics
    if not m or not result.trades:
        return ["Not enough data to draw insights."]

    # --- regime performance --------------------------------------------
    regimes = _classify_regime(price_series)
    pnl_by_regime: Dict[str, float] = {"bullish": 0, "bearish": 0, "sideways": 0}
    n_by_regime: Dict[str, int] = {"bullish": 0, "bearish": 0, "sideways": 0}
    for t in result.trades:
        try:
            r = regimes.asof(t.entry_time)
        except KeyError:
            continue
        if r in pnl_by_regime:
            pnl_by_regime[r] += t.pnl
            n_by_regime[r] += 1
    best = max(pnl_by_regime, key=pnl_by_regime.get)
    worst = min(pnl_by_regime, key=pnl_by_regime.get)
    if pnl_by_regime[best] > 0:
        out.append(f"Strategy performs best during **{best}** markets "
                   f"(${pnl_by_regime[best]:.0f} across {n_by_regime[best]} trades).")
    if pnl_by_regime[worst] < 0:
        out.append(f"Most losses occur during **{worst}** markets "
                   f"(${pnl_by_regime[worst]:.0f} across {n_by_regime[worst]} trades).")

    # --- drawdown vs leverage ------------------------------------------
    if abs(m["max_drawdown"]) > 0.25:
        out.append(
            f"Max drawdown is {m['max_drawdown']*100:.1f}% — "
            f"consider lowering risk-per-trade (currently {result.config.risk_per_trade*100:.1f}%) "
            f"or reducing leverage from {result.config.leverage}x."
        )

    # --- win-rate vs RR -------------------------------------------------
    if m["win_rate"] < 0.4 and m["risk_reward"] < 1.5:
        out.append(
            f"Win-rate {m['win_rate']*100:.1f}% with R:R {m['risk_reward']:.2f} is fragile — "
            f"try widening take-profit or tightening stop-loss to lift expectancy."
        )

    # --- profit factor --------------------------------------------------
    if m["profit_factor"] < 1.2 and m["total_trades"] >= 20:
        out.append(
            f"Profit factor {m['profit_factor']:.2f} is marginal — "
            f"the edge per trade is small; consider adding a trend filter."
        )

    # --- trade frequency ------------------------------------------------
    bars = len(result.equity)
    if m["total_trades"] / max(bars, 1) < 0.02:
        out.append("Very few trades — relax entry thresholds (e.g. raise RSI buy-below from 30 to 35).")
    elif m["total_trades"] / max(bars, 1) > 0.3:
        out.append("Trade frequency is high — fees and slippage will eat into returns; consider stricter filters.")

    # --- streaks --------------------------------------------------------
    if m["longest_loss_streak"] >= 5:
        out.append(
            f"Longest losing streak is {m['longest_loss_streak']} — "
            f"add a circuit-breaker that pauses trading after N consecutive losses."
        )

    # --- sharpe quality -------------------------------------------------
    if m["sharpe_ratio"] > 1.5:
        out.append(f"Sharpe {m['sharpe_ratio']:.2f} is strong — promote this configuration to paper trading.")
    elif m["sharpe_ratio"] < 0.5:
        out.append(f"Sharpe {m['sharpe_ratio']:.2f} is weak — risk-adjusted returns do not justify deployment.")

    return out or ["Strategy is balanced; no obvious improvements detected."]
