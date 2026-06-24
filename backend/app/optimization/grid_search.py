"""Grid-search optimiser.

Sweeps a parameter grid, scores every configuration with a chosen
objective, and returns a ranked DataFrame plus the best result.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Callable, Dict, Iterable, List

import pandas as pd

from ..engine import BacktestConfig, BacktestEngine, BacktestResult
from ..strategies import get_strategy


Objective = Callable[[BacktestResult], float]


def sharpe_objective(r: BacktestResult) -> float:
    return r.metrics.get("sharpe_ratio", 0.0) or 0.0


def calmar_objective(r: BacktestResult) -> float:
    return r.metrics.get("calmar_ratio", 0.0) or 0.0


def total_return_objective(r: BacktestResult) -> float:
    return r.metrics.get("total_return", 0.0) or 0.0


@dataclass
class OptimisationReport:
    table: pd.DataFrame
    best_params: Dict
    best_result: BacktestResult


def grid_search(
    df: pd.DataFrame,
    strategy_name: str,
    param_grid: Dict[str, Iterable],
    cfg: BacktestConfig,
    objective: Objective = sharpe_objective,
) -> OptimisationReport:
    keys = list(param_grid.keys())
    rows: List[Dict] = []
    best_score = float("-inf")
    best_result: BacktestResult | None = None
    best_params: Dict = {}

    for values in product(*[list(param_grid[k]) for k in keys]):
        params = dict(zip(keys, values))
        strat = get_strategy(strategy_name, **params)
        engine = BacktestEngine(cfg)
        result = engine.run(df, strat)
        score = objective(result)
        row = {**params, **{
            k: v for k, v in result.metrics.items()
            if k not in {"drawdown_series"}
        }, "objective": score}
        rows.append(row)
        if score > best_score:
            best_score = score
            best_result = result
            best_params = params

    table = pd.DataFrame(rows).sort_values("objective", ascending=False).reset_index(drop=True)
    return OptimisationReport(table=table, best_params=best_params, best_result=best_result)
