import pytest


def _has_request_id_header(headers) -> bool:
    return "x-request-id" in {k.lower(): v for k, v in headers.items()}


def test_list_payments_returns_list_and_request_id_header(client):
    r = client.get("/api/v1/payments")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert _has_request_id_header(r.headers)


def test_list_payments_filter_by_invoice_id_behaves(client):
    r_all = client.get("/api/v1/payments")
    assert r_all.status_code == 200
    payments = r_all.json()

    if not payments:
        pytest.skip("No payments in DB; cannot validate invoice_id filter without seeded payments.")

    invoice_id = payments[0].get("invoice_id")
    assert invoice_id is not None

    r = client.get(f"/api/v1/payments?invoice_id={invoice_id}")
    assert r.status_code == 200
    filtered = r.json()
    assert isinstance(filtered, list)
    assert all(p.get("invoice_id") == invoice_id for p in filtered)


def test_list_payments_422_validation_error_has_standard_shape(client):
    r = client.get("/api/v1/payments?invoice_id=-1")
    assert r.status_code == 422

    body = r.json()
    assert body["code"] == "REQUEST_VALIDATION_ERROR"
    assert body["message"] == "Invalid request"
    assert "errors" in body["details"]
    assert "request_id" in body["details"]
    assert "timestamp" in body
