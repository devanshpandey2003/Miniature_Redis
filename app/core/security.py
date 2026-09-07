"""
Simple shared-secret auth: the client sends `X-API-Key: <key>` on every
request. This is FastAPI's dependency-injection system doing what
middleware or a decorator would do elsewhere -- any route that adds
`Depends(require_api_key)` to its signature gets this check for free.
"""
from fastapi import Header, HTTPException, status
from app.config import settings


async def require_api_key(x_api_key: str = Header(...)) -> None:
    """
    FastAPI reads the `X-API-Key` HTTP header and passes it in as
    `x_api_key` automatically -- that's what `Header(...)` does. The `...`
    means the header is required; a missing header becomes an automatic
    422 error before this function even runs.
    """
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid API key",
        )
