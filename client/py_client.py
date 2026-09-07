"""
Equivalent of the blog's `Client` class -- a thin Python wrapper so you can
drive the server from a script or REPL without hand-writing HTTP calls
every time. There, it spoke raw RESP over a socket; here it speaks JSON
over HTTP via `httpx`.
"""

import httpx


class MiniRedisClient:
    def __init__(
        self, base_url: str = "http://localhost:8000", api_key: str | None = None
    ):
        headers = {"X-API-Key": api_key} if api_key else {}
        self._client = httpx.Client(base_url=base_url, headers=headers)

    def get(self, key: str):
        resp = self._client.get("/keys/{key}")
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()["value"]

    def set(self, key: str, value, ttl: int | None = None):
        resp = self._client.put(f"/keys/{key}", json={"value": value, "ttl": ttl})
        resp.raise_for_status()
        return resp.json()["ok"]

    def delete(self, key: str) -> bool:
        resp = self._client.delete(f"/keys/{key}")
        resp.raise_for_status()
        return resp.json()["deleted"]

    def mget(self, *keys: str) -> dict:
        resp = self._client.post("/keys/mget", json=list(keys))
        resp.raise_for_status()
        return resp.json()

    def mset(self, items: dict) -> int:
        resp = self._client.post("/keys/mset", json={"items": items})
        resp.raise_for_status()
        return resp.json()["count"]

    def incr(self, key: str, amount: int = 1) -> int:
        resp = self._client.post(f"/keys/{key}/incr", json={"amount": amount})
        resp.raise_for_status()
        return resp.json()["value"]

    def ttl(self, key: str) -> int:
        resp = self._client.get(f"/keys/{key}/ttl")
        resp.raise_for_status()
        return resp.json()["ttl"]

    def expire(self, key: str, ttl: int) -> bool:
        resp = self._client.post(f"/keys/{key}/expire", json={"ttl": ttl})
        return resp.status_code == 200

    def keys(self) -> list[str]:
        resp = self._client.get("/keys")
        resp.raise_for_status()
        return resp.json()["keys"]

    def flush(self) -> int:
        resp = self._client.post("/flush")
        resp.raise_for_status()
        return resp.json()["cleared"]

    def publish(self, channel: str, message: dict) -> int:
        resp = self._client.post(f"/publish/{channel}", json={"message": message})
        resp.raise_for_status()
        return resp.json()["delivered_to"]


if __name__ == "__main__":
    # Same interactive demo style as the original blog's REPL walkthrough.
    client = MiniRedisClient(api_key="dev-secret-key")
    client.mset({"k1": "v1", "k2": ["v2-0", 1, "v2-2"], "k3": "v3"})
    print(client.get("k2"))
    print(client.mget("k3", "k1"))
    client.delete("k1")
    client.set("kx", {"vx": {"vy": 0, "vz": [1, 2, 3]}})
    print(client.get("kx"))
