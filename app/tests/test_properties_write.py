import pytest


def test_create_property_ok(client):
    r_cust = client.get("/api/v1/customers")
    assert r_cust.status_code == 200
    customers = r_cust.json()

    if not customers:
        pytest.skip("No customers in DB; cannot test creating property without seeding a customer.")

    customer_id = customers[0]["customer_id"]

    payload = {
        "customer_id": customer_id,
        "label": "Main House",
        "address1": "123 Test St",
        "city": "Rincon",
        "state": "PR",
        "postal_code": "00677",
        "notes": "pytest",
        "is_active": 1,
    }

    r = client.post("/api/v1/properties", json=payload)
    assert r.status_code in (200, 201)
    body = r.json()
    assert body["customer_id"] == customer_id
    assert body["label"] == payload["label"]


def test_create_property_validation_error_422_standard_shape(client):
    payload = {
        "customer_id": "nope",
        "label": "X",
        "address1": "Y",
        "is_active": 1,
    }

    r = client.post("/api/v1/properties", json=payload)
    assert r.status_code == 422

    body = r.json()
    assert body["code"] == "REQUEST_VALIDATION_ERROR"
    assert body["message"] == "Invalid request"
    assert "details" in body and "errors" in body["details"]
    assert "request_id" in body["details"]
    assert "timestamp" in body
