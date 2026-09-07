"""
The application entrypoint. This is the FastAPI-native equivalent of the
blog's:

    if __name__ == '__main__':
        from gevent import monkey; monkey.patch_all()
        server = Server()
        server.run()

Instead of one Server class doing everything, we assemble routers (each
handling one concern) and kick off the background worker + AOF replay
using FastAPI's lifespan events.
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.config import settings
from app.api.deps import get_store, get_aof_logger
from app.api.routes import keys, admin, pubsub
from app.workers.expiry import expiry_sweeper


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ----- STARTUP -----
    store = get_store()
    aof = get_aof_logger()

    replayed = await aof.replay(store)          # rebuild state from disk
    print(f"[startup] replayed {replayed} command(s) from AOF")

    sweeper_task = asyncio.create_task(
        expiry_sweeper(store, interval=settings.expiry_sweep_interval)
    )

    yield  # <-- application runs while suspended here

    # ----- SHUTDOWN -----
    sweeper_task.cancel()
    try:
        await sweeper_task
    except asyncio.CancelledError:
        pass
    print("[shutdown] expiry sweeper stopped")


app = FastAPI(title="Mini Redis (FastAPI)", lifespan=lifespan)

# Each router owns one URL prefix / concern -- this is the "dispatch table"
# from the original blog, just expressed as FastAPI's routing system.
app.include_router(keys.router)
app.include_router(admin.router)
app.include_router(pubsub.router)


@app.get("/")
async def root():
    return {"service": "mini-redis-fastapi", "status": "ok"}
