def test_list_customers_returns_list_and_request_id_header(client):
    r = client.get("/api/v1/customers")
    assert r.status_code == 200

    data = r.json()
    assert isinstance(data, list)

    assert "x-request-id" in {k.lower(): v for k, v in r.headers.items()}


def test_get_customer_404_uses_standard_error_shape(client):
    missing_id = 100

    r = client.get(f"/api/v1/customers/{missing_id}")
    assert r.status_code == 404

    body = r.json()
    assert body["code"] == "HTTP_404"
    assert "message" in body
    assert "details" in body
    assert "request_id" in body["details"]
    assert "timestamp" in body


def test_get_customer_422_validation_error_has_standard_shape(client):
    r = client.get("/api/v1/customers/99999")
    assert r.status_code == 422

    body = r.json()
    assert body["code"] == "REQUEST_VALIDATION_ERROR"
    assert body["message"] == "Invalid request"
    assert "details" in body
    assert "errors" in body["details"]
    assert "request_id" in body["details"]
    assert "timestamp" in body
