"""
The actual "database". This class has ZERO knowledge of FastAPI, HTTP, or
JSON — it's pure Python, which means you can unit test it directly with
plain pytest, no web server needed. This mirrors the blog's `self._kv = {}`
dict, but adds TTL (expiry) support and an asyncio.Lock for safe concurrent
mutation.
"""
import time
import asyncio
from typing import Any, Optional


class KVStore:
    def __init__(self):
        # The actual data. Values can be any JSON-serializable Python object
        # (str, int, list, dict) -- same idea as the original _write()'s
        # support for multiple types.
        self._data: dict[str, Any] = {}

        # key -> unix timestamp when it should expire. Keys with no entry
        # here never expire.
        self._expires: dict[str, float] = {}

        # Guards every read-modify-write against interleaving from another
        # coroutine. gevent's cooperative scheduling made this implicit in
        # the original; asyncio needs it explicit whenever you have more
        # than one step between "check" and "act".
        self._lock = asyncio.Lock()

    def _is_expired(self, key: str) -> bool:
        exp = self._expires.get(key)
        return exp is not None and time.time() >= exp

    async def get(self, key: str) -> Optional[Any]:
        """Equivalent of the blog's `get()`. Returns None if missing or expired."""
        async with self._lock:
            if key in self._data and self._is_expired(key):
                del self._data[key]
                del self._expires[key]
                return None
            return self._data.get(key)

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Equivalent of the blog's `set()`, plus an optional ttl in seconds.
        Setting a key with no ttl clears any previous expiry (matches real
        Redis semantics: SET without EX removes the old TTL).
        """
        async with self._lock:
            self._data[key] = value
            if ttl is not None:
                self._expires[key] = time.time() + ttl
            else:
                self._expires.pop(key, None)
            return True

    async def delete(self, key: str) -> bool:
        """Equivalent of the blog's `delete()`. Returns True if key existed."""
        async with self._lock:
            existed = key in self._data
            self._data.pop(key, None)
            self._expires.pop(key, None)
            return existed

    async def mget(self, keys: list[str]) -> list[Optional[Any]]:
        """Equivalent of the blog's `mget()`."""
        return [await self.get(k) for k in keys]

    async def mset(self, items: dict[str, Any]) -> int:
        """Equivalent of the blog's `mset()`."""
        for k, v in items.items():
            await self.set(k, v)
        return len(items)

    async def flush(self) -> int:
        """Equivalent of the blog's `flush()`. Wipes everything, returns count removed."""
        async with self._lock:
            count = len(self._data)
            self._data.clear()
            self._expires.clear()
            return count

    async def incr(self, key: str, amount: int = 1) -> int:
        """New: atomic increment. Raises if the existing value isn't an int."""
        async with self._lock:
            current = self._data.get(key, 0)
            if not isinstance(current, int):
                raise TypeError(f"value at '{key}' is not an integer")
            new_value = current + amount
            self._data[key] = new_value
            return new_value

    async def ttl(self, key: str) -> int:
        """
        New: mirrors real Redis TTL semantics.
        -2 = key doesn't exist, -1 = key exists but has no expiry,
        otherwise seconds remaining.
        """
        async with self._lock:
            if key not in self._data or self._is_expired(key):
                return -2
            if key not in self._expires:
                return -1
            return max(0, int(self._expires[key] - time.time()))

    async def expire(self, key: str, ttl: int) -> bool:
        """New: attach a TTL to an already-existing key."""
        async with self._lock:
            if key not in self._data:       
                return False
            self._expires[key] = time.time() + ttl
            return True

    async def keys(self) -> list[str]:
        """New: list all non-expired keys (careful with this in real usage -- O(n))."""
        async with self._lock:
            now = time.time()
            return [
                k for k in self._data
                if self._expires.get(k, float("inf")) > now
            ]

    async def type_of(self, key: str) -> Optional[str]:
        """New: report the Python type name of a stored value, like Redis's TYPE."""
        value = await self.get(key)
        if value is None:
            return None
        return type(value).__name__

    async def sweep_expired(self) -> int:
        """
        Called periodically by the background worker (workers/expiry.py).
        Actively evicts expired keys rather than waiting for someone to
        touch them. Returns how many were removed.
        """
        async with self._lock:
            now = time.time()
            expired = [k for k, exp in self._expires.items() if now >= exp]
            for k in expired:
                self._data.pop(k, None)
                self._expires.pop(k, None)
            return len(expired)


# A single, shared, process-wide store instance.
# FastAPI's dependency (app/api/deps.py) hands this out to every route.
store = KVStore()
