"""Core technical-indicator implementations.

All functions accept a pandas DataFrame with OHLCV columns
(`open, high, low, close, volume`) or a pandas Series and return
a Series / DataFrame indexed the same way.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def sma(series: pd.Series, length: int = 20) -> pd.Series:
    return series.rolling(length, min_periods=length).mean()


def ema(series: pd.Series, length: int = 20) -> pd.Series:
    return series.ewm(span=length, adjust=False, min_periods=length).mean()


def rsi(series: pd.Series, length: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()
    avg_loss = loss.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return (100 - (100 / (1 + rs))).fillna(50)


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    fast_ema = ema(series, fast)
    slow_ema = ema(series, slow)
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal, adjust=False, min_periods=signal).mean()
    hist = macd_line - signal_line
    return pd.DataFrame({"macd": macd_line, "signal": signal_line, "hist": hist})


def bollinger_bands(series: pd.Series, length: int = 20, mult: float = 2.0) -> pd.DataFrame:
    mid = sma(series, length)
    std = series.rolling(length, min_periods=length).std()
    upper = mid + mult * std
    lower = mid - mult * std
    return pd.DataFrame({"bb_upper": upper, "bb_mid": mid, "bb_lower": lower})


def atr(df: pd.DataFrame, length: int = 14) -> pd.Series:
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = pd.concat(
        [(high - low).abs(), (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()


def vwap(df: pd.DataFrame) -> pd.Series:
    tp = (df["high"] + df["low"] + df["close"]) / 3.0
    pv = tp * df["volume"]
    return pv.cumsum() / df["volume"].cumsum().replace(0, np.nan)


def stoch_rsi(series: pd.Series, length: int = 14, k: int = 3, d: int = 3) -> pd.DataFrame:
    rsi_series = rsi(series, length)
    lowest = rsi_series.rolling(length, min_periods=length).min()
    highest = rsi_series.rolling(length, min_periods=length).max()
    stoch = ((rsi_series - lowest) / (highest - lowest).replace(0, np.nan)) * 100
    k_line = stoch.rolling(k, min_periods=k).mean()
    d_line = k_line.rolling(d, min_periods=d).mean()
    return pd.DataFrame({"stoch_rsi": stoch, "k": k_line, "d": d_line})


def volume_rising(volume: pd.Series, length: int = 20) -> pd.Series:
    """Boolean series: current volume above its `length`-period SMA."""
    return volume > sma(volume, length)


def momentum(series: pd.Series, length: int = 10) -> pd.Series:
    return series.pct_change(length) * 100
