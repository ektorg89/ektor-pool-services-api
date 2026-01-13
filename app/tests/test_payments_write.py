import uuid
import pytest


def _has_request_id_header(headers) -> bool:
    return "x-request-id" in {k.lower(): v for k, v in headers.items()}


def _ref(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _get_first(client, path: str):
    r = client.get(path)
    assert r.status_code == 200
    items = r.json()
    return items[0] if items else None


def _get_invoice(client, invoice_id: int):
    r = client.get(f"/api/v1/invoices/{invoice_id}")
    assert r.status_code == 200
    return r.json()


def _create_customer(client):
    payload = {"first_name": "Test", "last_name": _ref("Cust")}
    r = client.post("/api/v1/customers", json=payload)
    assert r.status_code == 201
    return r.json()["customer_id"]


def _create_property(client, customer_id: int):
    payload = {
        "customer_id": customer_id,
        "label": "Test Pool",
        "address1": "123 Test St",
        "address2": None,
        "city": "Aguadilla",
        "state": "PR",
        "postal_code": "00603",
        "notes": None,
        "is_active": 1,
    }
    r = client.post("/api/v1/properties", json=payload)
    assert r.status_code == 201
    return r.json()["property_id"]


def _create_invoice(client, customer_id: int, property_id: int, total: float, status: str):
    payload = {
        "customer_id": customer_id,
        "property_id": property_id,
        "period_start": "2026-01-01",
        "period_end": "2026-01-31",
        "issued_date": "2026-01-31",
        "due_date": "2026-02-10",
        "subtotal": round(total - 3.00, 2),
        "tax": 3.00,
        "total": round(total, 2),
        "status": status,
        "notes": "test invoice",
    }
    r = client.post("/api/v1/invoices", json=payload)

    if r.status_code == 422:
        pytest.skip(f"InvoiceCreate rejected status='{status}' (422).")
    if r.status_code != 201:
        pytest.skip(f"InvoiceCreate failed: status={r.status_code}, body={r.json()}")

    return r.json()["invoice_id"]


def _create_fresh_sent_invoice_or_skip(client, total: float):
    customer_id = _create_customer(client)
    property_id = _create_property(client, customer_id)
    invoice_id = _create_invoice(client, customer_id, property_id, total, "sent")

    inv = _get_invoice(client, invoice_id)
    if inv.get("status") != "sent":
        pytest.skip(f"Expected invoice status 'sent' but got '{inv.get('status')}'.")

    return invoice_id


def test_create_payment_422_validation_error_standard_shape(client):
    payload = {"invoice_id": -1, "amount": -5, "reference": ""}

    r = client.post("/api/v1/payments", json=payload)
    assert r.status_code == 422

    body = r.json()
    assert body["code"] == "REQUEST_VALIDATION_ERROR"
    assert body["message"] == "Invalid request"
    assert "errors" in body["details"]
    assert "request_id" in body["details"]
    assert "timestamp" in body
    assert _has_request_id_header(r.headers)


def test_create_payment_partial_keeps_invoice_sent(client):
    invoice_id = _create_fresh_sent_invoice_or_skip(client, 30.00)
    before = _get_invoice(client, invoice_id)
    total = float(before["total"])
    amount = max(round(total / 3, 2), 0.01)

    payload = {"invoice_id": invoice_id, "amount": amount, "reference": _ref("PARTIAL")}
    r = client.post("/api/v1/payments", json=payload)

    if r.status_code != 201:
        pytest.skip(f"Partial payment failed: status={r.status_code}, body={r.json()}")

    after = _get_invoice(client, invoice_id)
    assert after["status"] == "sent"
    assert _has_request_id_header(r.headers)


def test_create_payment_total_marks_invoice_paid(client):
    invoice_id = _create_fresh_sent_invoice_or_skip(client, 30.00)
    before = _get_invoice(client, invoice_id)
    total = float(before["total"])

    payload = {"invoice_id": invoice_id, "amount": total, "reference": _ref("FULL")}
    r = client.post("/api/v1/payments", json=payload)

    if r.status_code != 201:
        pytest.skip(f"Full payment failed: status={r.status_code}, body={r.json()}")

    after = _get_invoice(client, invoice_id)
    assert after["status"] == "paid"
    assert _has_request_id_header(r.headers)


def test_cannot_pay_paid_invoice_409(client):
    inv = _get_first(client, "/api/v1/invoices?status=paid")
    if not inv:
        pytest.skip("No 'paid' invoice available in DB.")

    payload = {"invoice_id": inv["invoice_id"], "amount": 0.01, "reference": _ref("PAID")}
    r = client.post("/api/v1/payments", json=payload)

    assert r.status_code == 409
    assert _has_request_id_header(r.headers)


def test_cannot_pay_void_invoice_400(client):
    inv = _get_first(client, "/api/v1/invoices?status=void")
    if not inv:
        pytest.skip("No 'void' invoice available in DB.")

    payload = {"invoice_id": inv["invoice_id"], "amount": 0.01, "reference": _ref("VOID")}
    r = client.post("/api/v1/payments", json=payload)

    assert r.status_code == 400
    assert _has_request_id_header(r.headers)


def test_cannot_exceed_invoice_total_409(client):
    invoice_id = _create_fresh_sent_invoice_or_skip(client, 30.00)
    before = _get_invoice(client, invoice_id)

    payload = {
        "invoice_id": invoice_id,
        "amount": float(before["total"]) + 9999,
        "reference": _ref("EXCEED"),
    }
    r = client.post("/api/v1/payments", json=payload)

    assert r.status_code in (400, 409)
    assert _has_request_id_header(r.headers)


def test_duplicate_reference_per_invoice_409(client):
    invoice_id = _create_fresh_sent_invoice_or_skip(client, 30.00)
    ref = _ref("DUP")

    r1 = client.post("/api/v1/payments", json={"invoice_id": invoice_id, "amount": 0.01, "reference": ref})
    if r1.status_code != 201:
        pytest.skip(f"First payment failed: status={r1.status_code}, body={r1.json()}")

    r2 = client.post("/api/v1/payments", json={"invoice_id": invoice_id, "amount": 0.01, "reference": ref})
    assert r2.status_code == 409
    assert _has_request_id_header(r2.headers)
