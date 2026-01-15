import uuid
import pytest


def _has_request_id_header(headers) -> bool:
    return "x-request-id" in {k.lower(): v for k, v in headers.items()}


def _ref(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _create_customer(client):
    payload = {"first_name": "Test", "last_name": _ref("User")}
    r = client.post("/api/v1/customers", json=payload)
    assert r.status_code == 201, r.json()
    return r.json()["customer_id"]


def _create_property(client, customer_id: int):
    payload = {
        "customer_id": customer_id,
        "label": "Test Property",
        "address1": "123 Test St",
        "address2": None,
        "city": "Test City",
        "state": "PR",
        "postal_code": "00601",
        "notes": None,
        "is_active": True,
    }
    r = client.post("/api/v1/properties", json=payload)
    assert r.status_code == 201, r.json()
    return r.json()["property_id"]


def _create_invoice(client, customer_id: int, property_id: int, status: str, total: float = 30.00):
    tax = 3.00
    subtotal = round(total - tax, 2)

    payload = {
        "customer_id": customer_id,
        "property_id": property_id,
        "period_start": "2026-01-01",
        "period_end": "2026-01-31",
        "issued_date": "2026-01-31",
        "due_date": "2026-02-10",
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
        "status": status,
        "notes": "test invoice",
    }
    r = client.post("/api/v1/invoices", json=payload)
    assert r.status_code == 201, r.json()
    return r.json()["invoice_id"]


def _get_invoice(client, invoice_id: int):
    r = client.get(f"/api/v1/invoices/{invoice_id}")
    assert r.status_code == 200, r.json()
    return r.json()


def _create_sent_invoice(client, total: float = 30.00):
    customer_id = _create_customer(client)
    property_id = _create_property(client, customer_id)
    return _create_invoice(client, customer_id, property_id, status="sent", total=total)


def _create_void_invoice(client, total: float = 30.00):
    customer_id = _create_customer(client)
    property_id = _create_property(client, customer_id)
    return _create_invoice(client, customer_id, property_id, status="void", total=total)


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
    invoice_id = _create_sent_invoice(client, total=30.00)
    before = _get_invoice(client, invoice_id)
    total = float(before["total"])
    amount = max(round(total / 3, 2), 0.01)

    payload = {"invoice_id": invoice_id, "amount": amount, "reference": _ref("PARTIAL")}
    r = client.post("/api/v1/payments", json=payload)
    assert r.status_code == 201, r.json()
    assert _has_request_id_header(r.headers)

    after = _get_invoice(client, invoice_id)
    assert after["status"] == "sent"


def test_create_payment_total_marks_invoice_paid(client):
    invoice_id = _create_sent_invoice(client, total=30.00)
    before = _get_invoice(client, invoice_id)
    total = float(before["total"])

    payload = {"invoice_id": invoice_id, "amount": total, "reference": _ref("FULL")}
    r = client.post("/api/v1/payments", json=payload)
    assert r.status_code == 201, r.json()
    assert _has_request_id_header(r.headers)

    after = _get_invoice(client, invoice_id)
    assert after["status"] == "paid"


def test_cannot_pay_paid_invoice_409(client):
    invoice_id = _create_sent_invoice(client, total=30.00)
    total = float(_get_invoice(client, invoice_id)["total"])

    r1 = client.post("/api/v1/payments", json={"invoice_id": invoice_id, "amount": total, "reference": _ref("PAY")})
    assert r1.status_code == 201, r1.json()

    r2 = client.post("/api/v1/payments", json={"invoice_id": invoice_id, "amount": 0.01, "reference": _ref("PAY2")})
    assert r2.status_code == 409
    body = r2.json()
    assert "code" in body and "message" in body and "timestamp" in body
    assert _has_request_id_header(r2.headers)


def test_cannot_pay_void_invoice_400(client):
    invoice_id = _create_void_invoice(client, total=30.00)

    r = client.post("/api/v1/payments", json={"invoice_id": invoice_id, "amount": 0.01, "reference": _ref("VOID")})
    assert r.status_code == 400
    body = r.json()
    assert "code" in body and "message" in body and "timestamp" in body
    assert _has_request_id_header(r.headers)


def test_cannot_exceed_invoice_total_409(client):
    invoice_id = _create_sent_invoice(client, total=30.00)
    total = float(_get_invoice(client, invoice_id)["total"])

    payload = {"invoice_id": invoice_id, "amount": total + 9999, "reference": _ref("EXCEED")}
    r = client.post("/api/v1/payments", json=payload)

    assert r.status_code == 409
    body = r.json()
    assert "code" in body and "message" in body and "timestamp" in body
    assert _has_request_id_header(r.headers)


def test_duplicate_reference_per_invoice_409(client):
    invoice_id = _create_sent_invoice(client, total=30.00)
    ref = _ref("DUPREF")

    r1 = client.post("/api/v1/payments", json={"invoice_id": invoice_id, "amount": 0.01, "reference": ref})
    assert r1.status_code == 201, r1.json()

    r2 = client.post("/api/v1/payments", json={"invoice_id": invoice_id, "amount": 0.01, "reference": ref})
    assert r2.status_code == 409
    body = r2.json()
    assert "code" in body and "message" in body and "timestamp" in body
    assert _has_request_id_header(r2.headers)
