"""
Without this, expired keys are only cleaned up "lazily" -- i.e. the next
time someone calls get() on them. That's fine for correctness, but memory
for expired-but-untouched keys would never be reclaimed. This background
task actively sweeps them out on a timer, same as real Redis's active
expiry cycle.
"""
import asyncio
import logging

logger = logging.getLogger("mini_redis.expiry")


async def expiry_sweeper(store, interval: float = 1.0) -> None:
    """
    Runs forever in the background (started as an asyncio.Task at app
    startup). Every `interval` seconds, asks the store to evict anything
    past its expiry time.
    """
    while True:
        await asyncio.sleep(interval)
        removed = await store.sweep_expired()
        if removed:
            logger.info("swept %d expired key(s)", removed)
