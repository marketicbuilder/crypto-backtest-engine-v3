"""Performance metrics for an equity curve and a list of trades."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List

import numpy as np
import pandas as pd


@dataclass
class Trade:
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    side: str            # "long" | "short"
    entry_price: float
    exit_price: float
    qty: float
    pnl: float
    pnl_pct: float
    fees: float
    score: float
    reason_entry: str
    reason_exit: str

    def to_dict(self) -> Dict:
        d = self.__dict__.copy()
        d["entry_time"] = str(self.entry_time)
        d["exit_time"] = str(self.exit_time)
        return d


# ------------------------------------------------------------------ math
def _annualisation_factor(timestamps: pd.DatetimeIndex) -> float:
    """Approximate bars-per-year for any timeframe."""
    if len(timestamps) < 2:
        return 365.0
    dt = (timestamps[-1] - timestamps[0]) / max(len(timestamps) - 1, 1)
    seconds = dt.total_seconds() or 86400
    return (365.0 * 86400) / seconds


def sharpe(returns: pd.Series, periods_per_year: float, rf: float = 0.0) -> float:
    if returns.std(ddof=0) == 0 or returns.empty:
        return 0.0
    excess = returns - rf / periods_per_year
    return float(np.sqrt(periods_per_year) * excess.mean() / returns.std(ddof=0))


def sortino(returns: pd.Series, periods_per_year: float, rf: float = 0.0) -> float:
    if returns.empty:
        return 0.0
    downside = returns[returns < 0]
    if downside.empty:
        return 0.0
    dstd = downside.std(ddof=0)
    if dstd == 0 or not np.isfinite(dstd):
        return 0.0
    excess = returns - rf / periods_per_year
    return float(np.sqrt(periods_per_year) * excess.mean() / dstd)


def max_drawdown(equity: pd.Series) -> tuple[float, pd.Series]:
    peak = equity.cummax()
    dd = (equity - peak) / peak
    return float(dd.min()), dd


def streaks(trades: List[Trade]) -> tuple[int, int]:
    longest_win = longest_loss = cur_w = cur_l = 0
    for t in trades:
        if t.pnl > 0:
            cur_w += 1
            cur_l = 0
        elif t.pnl < 0:
            cur_l += 1
            cur_w = 0
        else:
            cur_w = cur_l = 0
        longest_win = max(longest_win, cur_w)
        longest_loss = max(longest_loss, cur_l)
    return longest_win, longest_loss


def compute_metrics(equity: pd.Series, trades: List[Trade], starting_balance: float) -> Dict:
    if equity.empty:
        return {}
    returns = equity.pct_change().fillna(0)
    ppy = _annualisation_factor(equity.index)
    total_return = float(equity.iloc[-1] / starting_balance - 1)
    years = max((equity.index[-1] - equity.index[0]).days / 365.25, 1e-9)
    annual_return = float((1 + total_return) ** (1 / years) - 1) if total_return > -1 else -1.0
    mdd, dd_series = max_drawdown(equity)

    wins = [t for t in trades if t.pnl > 0]
    losses = [t for t in trades if t.pnl < 0]
    total_trades = len(trades)
    win_rate = len(wins) / total_trades if total_trades else 0.0
    loss_rate = len(losses) / total_trades if total_trades else 0.0
    avg_win = float(np.mean([t.pnl for t in wins])) if wins else 0.0
    avg_loss = float(np.mean([t.pnl for t in losses])) if losses else 0.0
    rr = abs(avg_win / avg_loss) if avg_loss else math.inf if avg_win else 0.0
    gross_profit = sum(t.pnl for t in wins)
    gross_loss = -sum(t.pnl for t in losses)
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else (math.inf if gross_profit > 0 else 0.0)
    longest_win, longest_loss = streaks(trades)
    calmar = (annual_return / abs(mdd)) if mdd < 0 else 0.0

    return {
        "starting_balance": starting_balance,
        "final_balance": float(equity.iloc[-1]),
        "total_return": total_return,
        "annual_return": annual_return,
        "win_rate": win_rate,
        "loss_rate": loss_rate,
        "average_win": avg_win,
        "average_loss": avg_loss,
        "risk_reward": rr,
        "max_drawdown": mdd,
        "sharpe_ratio": sharpe(returns, ppy),
        "sortino_ratio": sortino(returns, ppy),
        "calmar_ratio": calmar,
        "profit_factor": profit_factor,
        "total_trades": total_trades,
        "longest_win_streak": longest_win,
        "longest_loss_streak": longest_loss,
        "drawdown_series": dd_series,
    }
