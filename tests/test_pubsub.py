from app.main import app


def test_publish_with_no_subscribers_delivers_to_zero(client):
    r = client.post("/publish/news", json={"message": {"hello": "world"}})
    assert r.status_code == 200
    assert r.json()["delivered_to"] == 0


def test_subscriber_receives_published_message():
    from fastapi.testclient import TestClient

    with TestClient(app) as c:
        with c.websocket_connect("/ws/subscribe/news") as ws:
            r = c.post("/publish/news", json={"message": {"headline": "big news"}})
            assert r.json()["delivered_to"] == 1

            data = ws.receive_json()
            assert data == {"headline": "big news"}
