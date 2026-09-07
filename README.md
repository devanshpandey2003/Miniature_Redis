# mini-redis

A small Redis-like key-value store, built on FastAPI. Adds TTL/expiry,
append-only-file persistence, WebSocket Pub/Sub, and API-key auth on top
of the core GET/SET/DELETE/MGET/MSET/FLUSH.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

Server starts at http://127.0.0.1:8000. Interactive API docs (auto-generated
by FastAPI) are at http://127.0.0.1:8000/docs.

## Try it

```bash
curl -X PUT localhost:8000/keys/name -H "Content-Type: application/json" -d '{"value": "Devansh"}'
curl localhost:8000/keys/name
curl -X POST localhost:8000/keys/counter/incr -H "Content-Type: application/json" -d '{"amount": 5}'
curl -X PUT localhost:8000/keys/temp -H "Content-Type: application/json" -d '{"value": "x", "ttl": 5}'
curl localhost:8000/keys/temp/ttl
curl localhost:8000/keys
curl -X POST localhost:8000/flush -H "X-API-Key: dev-secret-key"
```

Or use the Python client:

```bash
python3 client/py_client.py
```

## Pub/Sub

```bash
# Terminal 1: subscribe (requires a tool that speaks WebSocket, e.g. websocat)
websocat ws://localhost:8000/ws/subscribe/news

# Terminal 2: publish
curl -X POST localhost:8000/publish/news -H "Content-Type: application/json" \
  -d '{"message": {"headline": "hello"}}'
```

## Tests

```bash
pytest -v
```

## Endpoints

| Method | Path                  | Description                          |
|--------|-----------------------|---------------------------------------|
| GET    | /keys/{key}           | Get a value                           |
| PUT    | /keys/{key}           | Set a value (optional `ttl` seconds)  |
| DELETE | /keys/{key}           | Delete a key                          |
| POST   | /keys/mget            | Get multiple keys at once             |
| POST   | /keys/mset            | Set multiple keys at once             |
| POST   | /keys/{key}/incr      | Atomically increment an integer value |
| GET    | /keys/{key}/ttl       | Seconds until expiry (-1 none, -2 missing) |
| POST   | /keys/{key}/expire    | Attach a TTL to an existing key       |
| GET    | /keys                 | List all live keys                    |
| GET    | /type/{key}           | Python type name of a stored value    |
| POST   | /flush                | Wipe everything (requires X-API-Key)  |
| WS     | /ws/subscribe/{ch}    | Subscribe to a Pub/Sub channel        |
| POST   | /publish/{ch}         | Publish a message to a channel        |

## Notes on design

- `app/core/` has zero FastAPI imports -- it's pure Python, unit-testable
  without a running server.
- `app/api/routes/` stays thin: parse request -> call core -> return response.
- Persistence is a naive append-only JSON log (`app/core/persistence.py`),
  replayed on startup. No compaction -- a good next exercise.
- Expiry is both lazy (checked on read) and active (background sweep every
  second, see `app/workers/expiry.py`).
