"""Multi-factor AI scoring strategy.

Combines RSI, MACD, volume trend, momentum, Fear & Greed and news
sentiment into a 0-100 score that maps to BUY / HOLD / SELL.
Fear & Greed and news sentiment are optional columns; if absent we
neutralise the contribution so the strategy still works on raw OHLCV.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

import pandas as pd

from ..indicators import ema, macd, rsi, volume_rising
from .base import Signal, register


@dataclass
class AIScoringStrategy:
    name: str = "ai_scoring"
    params: Dict[str, float] = field(
        default_factory=lambda: {
            "rsi_length": 14,
            "rsi_buy_below": 35,
            "rsi_sell_above": 70,
            "ema_fast": 20,
            "ema_slow": 50,
            "vol_length": 20,
            "buy_threshold": 60,
            "sell_threshold": 40,
            "stop_loss_pct": 0.05,
            "take_profit_pct": 0.12,
        }
    )

    # ---- preparation -------------------------------------------------
    def prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        p = self.params
        out = df.copy()
        out["rsi"] = rsi(out["close"], int(p["rsi_length"]))
        m = macd(out["close"])
        out["macd"] = m["macd"]
        out["macd_signal"] = m["signal"]
        out["ema_fast"] = ema(out["close"], int(p["ema_fast"]))
        out["ema_slow"] = ema(out["close"], int(p["ema_slow"]))
        out["vol_rising"] = volume_rising(out["volume"], int(p["vol_length"]))
        out["mom"] = out["close"].pct_change(10) * 100
        # optional inputs default to neutral
        if "fear_greed" not in out:
            out["fear_greed"] = 50.0
        if "news_sent" not in out:
            out["news_sent"] = 0.0
        return out

    # ---- decision ----------------------------------------------------
    def decide(self, row: pd.Series, position: float) -> Signal:  # noqa: C901
        p = self.params
        breakdown: Dict[str, float] = {}
        reasons: list[str] = []

        # ---- RSI -----------------------------------------------------
        r = row.get("rsi")
        if pd.notna(r):
            if r < p["rsi_buy_below"]:
                breakdown["rsi_bullish"] = 20
                reasons.append(f"RSI {r:.1f} oversold (<{p['rsi_buy_below']})")
            elif r > p["rsi_sell_above"]:
                breakdown["rsi_bearish"] = -20
                reasons.append(f"RSI {r:.1f} overbought (>{p['rsi_sell_above']})")
            else:
                breakdown["rsi_neutral"] = 5
                reasons.append(f"RSI {r:.1f} neutral")

        # ---- MACD ----------------------------------------------------
        if pd.notna(row.get("macd")) and pd.notna(row.get("macd_signal")):
            if row["macd"] > row["macd_signal"]:
                breakdown["macd_bullish"] = 15
                reasons.append("MACD above signal (bullish)")
            else:
                breakdown["macd_bearish"] = -15
                reasons.append("MACD below signal (bearish)")

        # ---- Trend (EMA fast vs slow) --------------------------------
        if pd.notna(row.get("ema_fast")) and pd.notna(row.get("ema_slow")):
            if row["ema_fast"] > row["ema_slow"]:
                breakdown["trend_up"] = 10
                reasons.append("EMA-fast > EMA-slow (uptrend)")
            else:
                breakdown["trend_down"] = -10
                reasons.append("EMA-fast < EMA-slow (downtrend)")

        # ---- Volume --------------------------------------------------
        if bool(row.get("vol_rising", False)):
            breakdown["volume_rising"] = 10
            reasons.append("Volume above its 20-bar SMA")

        # ---- Momentum ------------------------------------------------
        mom = row.get("mom")
        if pd.notna(mom):
            if mom > 5:
                breakdown["momentum_strong"] = 10
                reasons.append(f"10-bar momentum +{mom:.1f}%")
            elif mom < -5:
                breakdown["momentum_weak"] = -10
                reasons.append(f"10-bar momentum {mom:.1f}%")

        # ---- Fear & Greed -------------------------------------------
        fg = float(row.get("fear_greed", 50))
        if fg < 25:
            breakdown["fear_extreme"] = 10
            reasons.append(f"Fear & Greed {fg:.0f} (extreme fear → contrarian buy)")
        elif fg > 75:
            breakdown["greed_extreme"] = -10
            reasons.append(f"Fear & Greed {fg:.0f} (extreme greed → caution)")
        else:
            breakdown["fg_neutral"] = 5

        # ---- News sentiment -----------------------------------------
        ns = float(row.get("news_sent", 0))
        if ns > 0.3:
            breakdown["news_positive"] = 15
            reasons.append("News sentiment positive")
        elif ns < -0.3:
            breakdown["news_negative"] = -15
            reasons.append("News sentiment negative")

        # ---- aggregate score ----------------------------------------
        raw = sum(breakdown.values())
        # map raw [-70..70] to 0..100 centred at 50
        score = max(0.0, min(100.0, 50.0 + raw))

        if score >= p["buy_threshold"]:
            action = "buy"
        elif score <= p["sell_threshold"]:
            action = "sell"
        else:
            action = "hold"

        # don't open a new long if we already are long, don't sell if flat
        if action == "buy" and position > 0:
            action = "hold"
        if action == "sell" and position <= 0:
            action = "hold"

        return Signal(
            action=action,
            score=score,
            reason="; ".join(reasons) or "no signal",
            breakdown=breakdown,
            stop_loss_pct=p["stop_loss_pct"],
            take_profit_pct=p["take_profit_pct"],
        )


@register("ai_scoring")
def _factory(**params) -> AIScoringStrategy:
    s = AIScoringStrategy()
    s.params.update({k: v for k, v in params.items() if k in s.params})
    return s
