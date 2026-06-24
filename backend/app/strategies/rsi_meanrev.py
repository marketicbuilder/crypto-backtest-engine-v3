"""RSI mean-reversion strategy."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

import pandas as pd

from ..indicators import rsi
from .base import Signal, register


@dataclass
class RsiMeanRevStrategy:
    name: str = "rsi_meanrev"
    params: Dict[str, float] = field(
        default_factory=lambda: {
            "length": 14,
            "buy_below": 30,
            "sell_above": 70,
            "stop_loss_pct": 0.05,
            "take_profit_pct": 0.08,
        }
    )

    def prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out["rsi"] = rsi(out["close"], int(self.params["length"]))
        return out

    def decide(self, row: pd.Series, position: float) -> Signal:
        r = row.get("rsi")
        if pd.isna(r):
            return Signal("hold", 50, "warming up")
        if r < self.params["buy_below"] and position <= 0:
            return Signal(
                "buy", 75,
                f"RSI {r:.1f} below {self.params['buy_below']} (oversold)",
                {"rsi_oversold": 25},
                stop_loss_pct=self.params["stop_loss_pct"],
                take_profit_pct=self.params["take_profit_pct"],
            )
        if r > self.params["sell_above"] and position > 0:
            return Signal(
                "sell", 25,
                f"RSI {r:.1f} above {self.params['sell_above']} (overbought)",
                {"rsi_overbought": -25},
            )
        return Signal("hold", 50, f"RSI {r:.1f} in neutral zone")


@register("rsi_meanrev")
def _factory(**params) -> RsiMeanRevStrategy:
    s = RsiMeanRevStrategy()
    s.params.update({k: v for k, v in params.items() if k in s.params})
    return s
