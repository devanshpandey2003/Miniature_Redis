import pytest
from app.core.store import KVStore
from app.core.persistence import AOFLogger


@pytest.mark.asyncio
async def test_append_and_replay(tmp_path):
    log_path = tmp_path / "test.aof"
    aof = AOFLogger(str(log_path))

    store = KVStore()
    await store.set("a", 1)
    await aof.append("SET", "a", 1)

    await store.set("b", [1, 2, 3])
    await aof.append("SET", "b", [1, 2, 3])

    await store.delete("a")
    await aof.append("DELETE", "a")

    # Simulate a restart: fresh store, replay the log into it.
    fresh_store = KVStore()
    replayed = await aof.replay(fresh_store)

    assert replayed == 3
    assert await fresh_store.get("a") is None       # was deleted
    assert await fresh_store.get("b") == [1, 2, 3]   # survived


@pytest.mark.asyncio
async def test_replay_on_missing_file_is_noop(tmp_path):
    aof = AOFLogger(str(tmp_path / "does-not-exist.aof"))
    store = KVStore()
    replayed = await aof.replay(store)
    assert replayed == 0
