"""Strategy registry endpoints."""
from fastapi import APIRouter

from ..strategies import get_strategy, list_strategies

router = APIRouter(prefix="/strategies", tags=["strategies"])


@router.get("")
def all_strategies() -> list[dict]:
    out = []
    for name in list_strategies():
        s = get_strategy(name)
        out.append({"name": name, "params": s.params})
    return out


@router.get("/{name}")
def strategy_detail(name: str) -> dict:
    s = get_strategy(name)
    return {"name": name, "params": s.params}
