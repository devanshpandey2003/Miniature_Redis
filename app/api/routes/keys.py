"""
Here, FastAPI's router does that dispatch for us based on
HTTP method + path -- GET /keys/x, PUT /keys/x, DELETE /keys/x, etc.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import get_store, get_aof_logger
from app.models.schemas import SetRequest, MSetRequest, IncrRequest, ExpireRequest

router = APIRouter(prefix="/keys", tags=["keys"])


@router.get("/{key}")
async def get_key(key: str, store=Depends(get_store)):
    """Equivalent of the blog's Client.get(key)."""
    value = await store.get(key)
    if value is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="key not found"
        )
    return {"key": key, "value": value}


@router.put("/{key}")
async def set_key(
    key: str,
    body: SetRequest,
    store=Depends(get_store),
    aof=Depends(get_aof_logger),
):
    """Equivalent of the blog's Client.set(key, value), plus optional ttl."""
    await store.set(key, body.value, ttl=body.ttl)
    await aof.append("SET", key, body.value)  # log AFTER the mutation succeeds
    return {"key": key, "ok": True}


@router.delete("/{key}")
async def delete_key(key: str, store=Depends(get_store), aof=Depends(get_aof_logger)):
    """Equivalent of the blog's Client.delete(key)."""
    existed = await store.delete(key)
    if existed:
        await aof.append("DELETE", key)
    return {"key": key, "deleted": existed}


@router.post("/mget")
async def mget_keys(keys: list[str], store=Depends(get_store)):
    """Equivalent of the blog's Client.mget(*keys). Body: ["k1", "k2"]"""
    values = await store.mget(keys)
    return dict(zip(keys, values))


@router.post("/mset")
async def mset_keys(
    body: MSetRequest, store=Depends(get_store), aof=Depends(get_aof_logger)
):
    """Equivalent of the blog's Client.mset(*items)."""
    count = await store.mset(body.items)
    for k, v in body.items.items():
        await aof.append("SET", k, v)
    return {"count": count}


@router.post("/{key}/incr")
async def incr_key(
    key: str,
    body: IncrRequest = IncrRequest(),
    store=Depends(get_store),
    aof=Depends(get_aof_logger),
):
    """New command: atomic increment, not present in the original blog post."""
    try:
        new_value = await store.incr(key, body.amount)
    except TypeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    await aof.append("INCR", key, body.amount)
    return {"key": key, "value": new_value}


@router.get("/{key}/ttl")
async def get_ttl(key: str, store=Depends(get_store)):
    """New: mirrors Redis's TTL command."""
    return {"key": key, "ttl": await store.ttl(key)}


@router.post("/{key}/expire")
async def set_expiry(key: str, body: ExpireRequest, store=Depends(get_store)):
    """New: mirrors Redis's EXPIRE command -- attach a TTL to an existing key."""
    ok = await store.expire(key, body.ttl)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="key not found"
        )
    return {"key": key, "ttl": body.ttl}
