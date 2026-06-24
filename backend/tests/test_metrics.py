import numpy as np
import pandas as pd

from app.engine.metrics import (Trade, compute_metrics, max_drawdown,
                                  sharpe, sortino, streaks)


def _eq(values):
    idx = pd.date_range("2024-01-01", periods=len(values), freq="1D", tz="UTC")
    return pd.Series(values, index=idx)


def test_sharpe_zero_when_constant():
    s = sharpe(_eq([0]*100).pct_change().fillna(0), 365)
    assert s == 0.0


def test_sortino_handles_no_negatives():
    s = sortino(_eq([100, 101, 102, 103]).pct_change().fillna(0), 365)
    assert s == 0.0  # downside std is zero


def test_max_drawdown_detects_correct_trough():
    mdd, dd = max_drawdown(_eq([100, 120, 90, 110, 60, 80]))
    assert abs(mdd - (60/120 - 1)) < 1e-9
    assert dd.iloc[0] == 0


def test_streaks_count():
    ts = pd.Timestamp("2024-01-01", tz="UTC")
    trades = []
    for pnl in [1, 1, -1, -1, -1, 1, -1, 1, 1, 1]:
        trades.append(Trade(ts, ts, "long", 100, 101 if pnl>0 else 99,
                            1, pnl, 0.01, 0, 0, "", ""))
    w, l = streaks(trades)
    assert w == 3
    assert l == 3


def test_compute_metrics_basic():
    eq = _eq(np.linspace(10_000, 11_000, 50))
    ts = pd.Timestamp("2024-01-01", tz="UTC")
    trades = [Trade(ts, ts, "long", 100, 110, 1, 10, 0.1, 0.1, 50, "", ""),
              Trade(ts, ts, "long", 100,  95, 1, -5, -0.05, 0.1, 50, "", "")]
    m = compute_metrics(eq, trades, 10_000)
    assert m["total_return"] > 0
    assert m["total_trades"] == 2
    assert m["win_rate"] == 0.5
