"""Strategy plug-in interface.

A strategy receives a row-level *context* (the current bar plus
pre-computed indicators) and returns a ``Signal``.  Concrete strategies
are registered with ``@register("name")`` so new ones can be added
without touching the engine.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Optional, Protocol

import pandas as pd


@dataclass
class Signal:
    """Single trading decision emitted by a strategy."""

    action: str              # "buy" | "sell" | "hold"
    score: float             # 0-100 confidence
    reason: str              # human-readable explanation
    breakdown: Dict[str, float] = field(default_factory=dict)
    stop_loss_pct: Optional[float] = None
    take_profit_pct: Optional[float] = None


class Strategy(Protocol):
    """Strategy plug-in contract.

    ``prepare`` is called once per backtest with the full OHLCV DataFrame
    and must return the same frame enriched with any indicator columns
    the strategy needs at decision time.

    ``decide`` is called for every bar with the enriched row and the
    current position size (>0 = long, <0 = short, 0 = flat).
    """

    name: str
    params: Dict[str, float]

    def prepare(self, df: pd.DataFrame) -> pd.DataFrame: ...

    def decide(self, row: pd.Series, position: float) -> Signal: ...


# ---------------------------------------------------------------- registry
_REGISTRY: Dict[str, Callable[..., Strategy]] = {}


def register(name: str) -> Callable[[Callable[..., Strategy]], Callable[..., Strategy]]:
    """Decorator to register a strategy factory under ``name``."""

    def wrap(factory: Callable[..., Strategy]) -> Callable[..., Strategy]:
        _REGISTRY[name] = factory
        return factory

    return wrap


def get_strategy(name: str, **params) -> Strategy:
    if name not in _REGISTRY:
        raise KeyError(f"unknown strategy '{name}'. available: {list(_REGISTRY)}")
    return _REGISTRY[name](**params)


def list_strategies() -> list[str]:
    return sorted(_REGISTRY.keys())
