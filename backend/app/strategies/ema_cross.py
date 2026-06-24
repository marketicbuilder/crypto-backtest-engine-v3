"""EMA crossover strategy — included to demonstrate the plug-in system."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

import pandas as pd

from ..indicators import ema
from .base import Signal, register


@dataclass
class EmaCrossStrategy:
    name: str = "ema_cross"
    params: Dict[str, float] = field(
        default_factory=lambda: {
            "fast": 12,
            "slow": 26,
            "stop_loss_pct": 0.04,
            "take_profit_pct": 0.10,
        }
    )

    def prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out["ema_fast"] = ema(out["close"], int(self.params["fast"]))
        out["ema_slow"] = ema(out["close"], int(self.params["slow"]))
        out["cross_up"] = (out["ema_fast"] > out["ema_slow"]) & (
            out["ema_fast"].shift(1) <= out["ema_slow"].shift(1)
        )
        out["cross_dn"] = (out["ema_fast"] < out["ema_slow"]) & (
            out["ema_fast"].shift(1) >= out["ema_slow"].shift(1)
        )
        return out

    def decide(self, row: pd.Series, position: float) -> Signal:
        if bool(row.get("cross_up")) and position <= 0:
            return Signal(
                action="buy", score=75,
                reason=f"EMA{int(self.params['fast'])} crossed above EMA{int(self.params['slow'])}",
                breakdown={"ema_cross_up": 25},
                stop_loss_pct=self.params["stop_loss_pct"],
                take_profit_pct=self.params["take_profit_pct"],
            )
        if bool(row.get("cross_dn")) and position > 0:
            return Signal(
                action="sell", score=25,
                reason=f"EMA{int(self.params['fast'])} crossed below EMA{int(self.params['slow'])}",
                breakdown={"ema_cross_dn": -25},
            )
        return Signal(action="hold", score=50, reason="no crossover")


@register("ema_cross")
def _factory(**params) -> EmaCrossStrategy:
    s = EmaCrossStrategy()
    s.params.update({k: v for k, v in params.items() if k in s.params})
    return s
