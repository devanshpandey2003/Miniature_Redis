import time


def test_ttl_on_key_with_no_expiry(client):
    client.put("/keys/foo", json={"value": "bar"})
    r = client.get("/keys/foo/ttl")
    assert r.json()["ttl"] == -1


def test_ttl_on_missing_key(client):
    r = client.get("/keys/nope/ttl")
    assert r.json()["ttl"] == -2


def test_key_expires_and_disappears(client):
    client.put("/keys/temp", json={"value": "x", "ttl": 1})
    assert client.get("/keys/temp").json()["value"] == "x"

    time.sleep(1.2)

    r = client.get("/keys/temp")
    assert r.status_code == 404


def test_expire_attaches_ttl_to_existing_key(client):
    client.put("/keys/foo", json={"value": "bar"})
    r = client.post("/keys/foo/expire", json={"ttl": 10})
    assert r.status_code == 200
    r = client.get("/keys/foo/ttl")
    assert 0 < r.json()["ttl"] <= 10


def test_expire_on_missing_key_returns_404(client):
    r = client.post("/keys/nope/expire", json={"ttl": 10})
    assert r.status_code == 404
