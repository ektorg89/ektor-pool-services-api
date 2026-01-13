import pytest


def _has_request_id_header(headers) -> bool:
    return "x-request-id" in {k.lower(): v for k, v in headers.items()}


def test_list_invoices_returns_list_and_request_id_header(client):
    r = client.get("/api/v1/invoices")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert _has_request_id_header(r.headers)


def test_list_invoices_filter_by_status_behaves(client):
    r_all = client.get("/api/v1/invoices")
    assert r_all.status_code == 200
    invoices = r_all.json()

    if not invoices:
        pytest.skip("No invoices in DB; cannot validate status filter without seeded invoices.")

    sample_status = invoices[0].get("status")
    assert sample_status is not None

    r = client.get(f"/api/v1/invoices?status={sample_status}")
    assert r.status_code == 200
    filtered = r.json()
    assert isinstance(filtered, list)
    assert all(inv.get("status") == sample_status for inv in filtered)


def test_get_invoice_detail_uses_real_id_when_available(client):
    r_all = client.get("/api/v1/invoices")
    assert r_all.status_code == 200
    invoices = r_all.json()

    if not invoices:
        pytest.skip("No invoices in DB; cannot validate invoice detail without seeded invoices.")

    invoice_id = invoices[0]["invoice_id"]

    r = client.get(f"/api/v1/invoices/{invoice_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["invoice_id"] == invoice_id
    assert _has_request_id_header(r.headers)


def test_get_invoice_404_or_422_has_standard_error_shape(client):
    r = client.get("/api/v1/invoices/999999")

    if r.status_code == 422:
        body = r.json()
        assert body["code"] == "REQUEST_VALIDATION_ERROR"
        assert "details" in body and "errors" in body["details"]
        return

    assert r.status_code == 404
    body = r.json()
    assert "code" in body
    assert "message" in body
    assert "details" in body and "request_id" in body["details"]
    assert "timestamp" in body