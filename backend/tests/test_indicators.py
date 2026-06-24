import numpy as np
import pandas as pd
import pytest

from app.indicators import (atr, bollinger_bands, ema, macd, momentum, rsi,
                             sma, stoch_rsi, vwap, volume_rising)


@pytest.fixture
def df() -> pd.DataFrame:
    rng = np.random.default_rng(7)
    n = 200
    close = 100 + np.cumsum(rng.normal(0, 1, n))
    high = close + np.abs(rng.normal(0, 0.5, n))
    low = close - np.abs(rng.normal(0, 0.5, n))
    open_ = close + rng.normal(0, 0.3, n)
    vol = np.abs(rng.normal(1000, 200, n))
    return pd.DataFrame({"open": open_, "high": high, "low": low,
                         "close": close, "volume": vol})


def test_sma_matches_rolling_mean(df):
    np.testing.assert_allclose(
        sma(df["close"], 20).dropna(),
        df["close"].rolling(20).mean().dropna(),
    )


def test_ema_finite(df):
    e = ema(df["close"], 20)
    assert e.dropna().shape[0] > 0
    assert np.isfinite(e.dropna()).all()


def test_rsi_bounded(df):
    r = rsi(df["close"], 14).dropna()
    assert (r >= 0).all() and (r <= 100).all()


def test_macd_columns(df):
    m = macd(df["close"])
    assert list(m.columns) == ["macd", "signal", "hist"]


def test_bbands_order(df):
    b = bollinger_bands(df["close"], 20, 2).dropna()
    assert (b["bb_upper"] >= b["bb_mid"]).all()
    assert (b["bb_lower"] <= b["bb_mid"]).all()


def test_atr_positive(df):
    a = atr(df, 14).dropna()
    assert (a > 0).all()


def test_vwap_finite(df):
    v = vwap(df).dropna()
    assert np.isfinite(v).all()


def test_stoch_rsi_bounded(df):
    s = stoch_rsi(df["close"], 14).dropna()
    assert (s["stoch_rsi"] >= 0).all() and (s["stoch_rsi"] <= 100).all()


def test_volume_rising_boolean(df):
    vr = volume_rising(df["volume"], 20)
    assert vr.dtype == bool


def test_momentum_signs(df):
    m = momentum(df["close"], 10)
    assert m.dtype.kind == "f"
