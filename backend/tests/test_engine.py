import numpy as np
import pandas as pd
import pytest

from app.engine import BacktestConfig, BacktestEngine
from app.strategies import get_strategy, list_strategies


@pytest.fixture
def df() -> pd.DataFrame:
    rng = np.random.default_rng(11)
    n = 400
    drift = 0.0005
    rets = rng.normal(drift, 0.02, n)
    close = 50_000 * np.exp(np.cumsum(rets))
    high = close * (1 + np.abs(rng.normal(0, 0.005, n)))
    low = close * (1 - np.abs(rng.normal(0, 0.005, n)))
    open_ = close * (1 + rng.normal(0, 0.002, n))
    vol = np.abs(rng.normal(1_000, 200, n))
    idx = pd.date_range("2023-01-01", periods=n, freq="1D", tz="UTC")
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": vol},
        index=idx,
    )


def test_all_strategies_registered():
    names = set(list_strategies())
    assert {"ai_scoring", "ema_cross", "rsi_meanrev"}.issubset(names)


@pytest.mark.parametrize("name", ["ai_scoring", "ema_cross", "rsi_meanrev"])
def test_strategy_runs(df, name):
    strat = get_strategy(name)
    res = BacktestEngine(BacktestConfig()).run(df, strat)
    assert len(res.equity) > 0
    assert "total_return" in res.metrics
    # equity starts at the configured balance
    assert abs(res.equity.iloc[0] - 10_000) < 10_000 * 0.05


def test_fees_and_slippage_reduce_pnl(df):
    strat_a = get_strategy("ema_cross")
    strat_b = get_strategy("ema_cross")
    r_no_fee = BacktestEngine(BacktestConfig(fee_pct=0, slippage_pct=0)).run(df, strat_a)
    r_fee = BacktestEngine(BacktestConfig(fee_pct=0.005, slippage_pct=0.002)).run(df, strat_b)
    if len(r_no_fee.trades) > 0 and len(r_fee.trades) > 0:
        assert r_no_fee.metrics["final_balance"] >= r_fee.metrics["final_balance"]


def test_stop_loss_caps_loss(df):
    strat = get_strategy("ai_scoring", buy_threshold=55, sell_threshold=45)
    cfg = BacktestConfig(starting_balance=10_000, stop_loss_pct=0.01,
                         take_profit_pct=0.50, risk_per_trade=0.10)
    res = BacktestEngine(cfg).run(df, strat)
    if res.trades:
        worst = min(t.pnl_pct for t in res.trades)
        # worst loss should be near the 1% SL plus fees/slippage, never -30%
        assert worst > -0.10
