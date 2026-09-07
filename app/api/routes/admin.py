"""
Operational endpoints -- listing keys, checking type, and wiping the store.
Grouped separately from keys.py because these are "operate on the whole
store" actions, not single-key CRUD.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import get_store, get_aof_logger
from app.core.security import require_api_key

router = APIRouter(tags=["admin"])


@router.get("/keys")
async def list_keys(store=Depends(get_store)):
    """New: list every live (non-expired) key."""
    return {"keys": await store.keys()}


@router.get("/type/{key}")
async def key_type(key: str, store=Depends(get_store)):
    """New: mirrors Redis's TYPE command."""
    t = await store.type_of(key)
    if t is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="key not found"
        )
    return {"key": key, "type": t}


@router.post("/flush", dependencies=[Depends(require_api_key)])
async def flush_store(store=Depends(get_store), aof=Depends(get_aof_logger)):
    """
    This wipes everything.
    Protected by an API key since it's destructive: notice
    `dependencies=[Depends(require_api_key)]` runs the check without the
    route needing to reference its return value.
    """
    count = await store.flush()
    await aof.append("FLUSH")
    return {"cleared": count}
