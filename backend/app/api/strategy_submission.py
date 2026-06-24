# NEW FILE - add to backend/app/routers/
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import importlib, sys, types, textwrap, re

router = APIRouter(prefix="/api/strategies", tags=["strategy-submission"])

# ── Tier 1: Average Trader (visual builder → auto-generated code) ──
class VisualStrategy(BaseModel):
    name: str
    indicator: str          # "rsi" | "ema_cross" | "macd" | "bbands"
    params: dict            # e.g. {"length":14,"buy_below":30,"sell_above":70}
    stop_loss_pct: float
    take_profit_pct: float

@router.post("/visual")
def submit_visual_strategy(payload: VisualStrategy):
    code = _generate_code(payload)
    return _register_dynamic(payload.name, code)

# ── Tier 2: Developer (paste raw Python) ──
class CodeStrategy(BaseModel):
    name: str
    code: str               # full Python class + @register decorator

@router.post("/code")
def submit_code_strategy(payload: CodeStrategy):
    _validate_code(payload.code)
    return _register_dynamic(payload.name, payload.code)

# ── Tier 3: Agent (same endpoint, machine-friendly) ──
# Agents just call POST /api/strategies/code with JSON body

# ── Shared helpers ──
def _generate_code(p: VisualStrategy) -> str:
    """Turns a VisualStrategy config into a valid strategy Python file."""
    if p.indicator == "rsi":
        decide_logic = f"""
        rsi = ta.rsi(df['close'], length={p.params.get('length', 14)}).iloc[-1]
        if position is None and rsi < {p.params.get('buy_below', 30)}:
            return Signal("buy", 80, "RSI oversold")
        if position == "long" and rsi > {p.params.get('sell_above', 70)}:
            return Signal("sell", 80, "RSI overbought")
        return Signal("hold", 50, "no signal")
"""
    elif p.indicator == "ema_cross":
        decide_logic = f"""
        fast = ta.ema(df['close'], length={p.params.get('fast', 9)}).iloc[-1]
        slow = ta.ema(df['close'], length={p.params.get('slow', 21)}).iloc[-1]
        if position is None and fast > slow:
            return Signal("buy", 75, "EMA cross up")
        if position == "long" and fast < slow:
            return Signal("sell", 75, "EMA cross down")
        return Signal("hold", 50, "no signal")
"""
    else:
        decide_logic = '        return Signal("hold", 50, "unsupported indicator")\n'

    return textwrap.dedent(f"""
from dataclasses import dataclass, field
import pandas_ta as ta
from .base import Signal, register

@dataclass
class {_class_name(p.name)}:
    name: str = "{p.name}"
    params: dict = field(default_factory=lambda: {p.params})
    stop_loss_pct: float = {p.stop_loss_pct}
    take_profit_pct: float = {p.take_profit_pct}

    def prepare(self, df):
        return df

    def decide(self, df, position):
{decide_logic}

@register("{p.name}")
def _factory(**params):
    return {_class_name(p.name)}(**params)
""")

def _class_name(name: str) -> str:
    return "".join(w.capitalize() for w in re.split(r'[_\-\s]', name))

def _validate_code(code: str):
    """Basic safety check — blocks obvious dangerous imports."""
    banned = ["import os", "import subprocess", "import sys", "__import__",
              "open(", "exec(", "eval("]
    for b in banned:
        if b in code:
            raise HTTPException(400, f"Disallowed pattern: {b}")

def _register_dynamic(name: str, code: str):
    """Compiles and registers the strategy into the live registry."""
    try:
        module = types.ModuleType(f"dynamic_strategy_{name}")
        exec(compile(code, f"<dynamic:{name}>", "exec"), module.__dict__)
        sys.modules[module.__name__] = module
        return {"status": "registered", "name": name}
    except Exception as e:
        raise HTTPException(400, f"Strategy compile error: {e}")
