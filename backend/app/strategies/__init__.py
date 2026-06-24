"""Strategy registry.

Importing this module triggers registration of all bundled strategies.
Third-party plug-ins can be loaded by calling ``load_plugins`` with a
list of dotted module paths.
"""
from importlib import import_module

from .base import Signal, Strategy, get_strategy, list_strategies, register

# Auto-register bundled strategies on import.
from . import ai_scoring as _ai_scoring  # noqa: F401
from . import ema_cross as _ema_cross    # noqa: F401
from . import rsi_meanrev as _rsi        # noqa: F401


def load_plugins(modules: list[str]) -> None:
    """Import additional strategy modules so their ``@register`` runs."""
    for m in modules:
        import_module(m)


__all__ = [
    "Signal", "Strategy", "get_strategy", "list_strategies",
    "register", "load_plugins",
]
