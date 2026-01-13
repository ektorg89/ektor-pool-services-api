def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200

    data = r.json()
    assert data["status"] == "ok"
    assert "version" in data

    assert "x-request-id" in {k.lower(): v for k, v in r.headers.items()}
