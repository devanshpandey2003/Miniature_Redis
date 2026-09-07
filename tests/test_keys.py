def test_set_and_get(client):
    r = client.put("/keys/foo", json={"value": "bar"})
    assert r.status_code == 200
    assert r.json() == {"key": "foo", "ok": True}

    r = client.get("/keys/foo")
    assert r.status_code == 200
    assert r.json()["value"] == "bar"


def test_get_missing_key_returns_404(client):
    r = client.get("/keys/does-not-exist")
    assert r.status_code == 404


def test_delete(client):
    client.put("/keys/foo", json={"value": "bar"})
    r = client.delete("/keys/foo")
    assert r.json() == {"key": "foo", "deleted": True}

    # deleting again should report deleted: False
    r = client.delete("/keys/foo")
    assert r.json()["deleted"] is False


def test_mset_and_mget(client):
    r = client.post("/keys/mset", json={"items": {"a": 1, "b": 2}})
    assert r.json()["count"] == 2

    r = client.post("/keys/mget", json=["a", "b", "missing"])
    assert r.json() == {"a": 1, "b": 2, "missing": None}


def test_incr(client):
    r = client.post("/keys/counter/incr", json={"amount": 5})
    assert r.json()["value"] == 5
    r = client.post("/keys/counter/incr", json={"amount": -2})
    assert r.json()["value"] == 3


def test_incr_on_non_int_fails(client):
    client.put("/keys/counter", json={"value": "not-a-number"})
    r = client.post("/keys/counter/incr", json={"amount": 1})
    assert r.status_code == 400


def test_list_keys_and_type(client):
    client.put("/keys/a", json={"value": [1, 2, 3]})
    r = client.get("/keys")
    assert "a" in r.json()["keys"]

    r = client.get("/type/a")
    assert r.json()["type"] == "list"


def test_flush_requires_api_key(client):
    r = client.post("/flush")
    assert r.status_code == 422  # missing header

    r = client.post("/flush", headers={"X-API-Key": "wrong"})
    assert r.status_code == 401

    client.put("/keys/a", json={"value": 1})
    r = client.post("/flush", headers={"X-API-Key": "dev-secret-key"})
    assert r.status_code == 200
    assert r.json()["cleared"] == 1
