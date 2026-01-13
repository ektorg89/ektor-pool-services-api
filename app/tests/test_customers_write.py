def test_create_customer_returns_201_and_persists_within_test_transaction(client):
    payload = {"first_name": "Ektor", "last_name": "Gonzalez"}

    r = client.post("/api/v1/customers", json=payload)
    assert r.status_code == 201

    body = r.json()
    assert "customer_id" in body
    assert body["first_name"] == payload["first_name"]
    assert body["last_name"] == payload["last_name"]

    customer_id = body["customer_id"]
    r2 = client.get(f"/api/v1/customers/{customer_id}")
    assert r2.status_code == 200
    body2 = r2.json()
    assert body2["customer_id"] == customer_id
    assert body2["first_name"] == payload["first_name"]
    assert body2["last_name"] == payload["last_name"]


def test_create_customer_validation_error_422_standard_shape(client):
    payload = {"first_name": 123, "last_name": "X"}

    r = client.post("/api/v1/customers", json=payload)
    assert r.status_code == 422

    body = r.json()
    assert body["code"] == "REQUEST_VALIDATION_ERROR"
    assert body["message"] == "Invalid request"
    assert "details" in body
    assert "errors" in body["details"]
    assert "request_id" in body["details"]
    assert "timestamp" in body
