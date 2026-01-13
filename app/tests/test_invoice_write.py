import pytest


def _has_request_id_header(headers) -> bool:
    return "x-request-id" in {k.lower(): v for k, v in headers.items()}


def _assert_standard_error_shape(body: dict):
    assert "code" in body
    assert "message" in body
    assert "details" in body
    assert "timestamp" in body
    assert isinstance(body["details"], dict)
    assert "request_id" in body["details"]


def _openapi(client) -> dict:
    r = client.get("/openapi.json")
    assert r.status_code == 200
    return r.json()


def _resolve_ref(spec: dict, ref: str) -> dict:
    assert ref.startswith("#/")
    cur = spec
    for part in ref.lstrip("#/").split("/"):
        cur = cur[part]
    return cur


def _schema_for_post_invoices(spec: dict) -> dict:
    op = spec["paths"]["/api/v1/invoices"]["post"]
    schema = op["requestBody"]["content"]["application/json"]["schema"]
    if "$ref" in schema:
        schema = _resolve_ref(spec, schema["$ref"])
    return schema


def _pick_minimal_payload_from_schema(schema: dict, base: dict) -> dict:
   
    props = schema.get("properties", {})
    required = schema.get("required", [])

    payload = dict(base)

    def set_if_needed(name: str, value):
        if name in required and name not in payload:
            payload[name] = value

    set_if_needed("status", "draft")
    set_if_needed("subtotal", 100.0)
    set_if_needed("tax", 0.0)
    set_if_needed("total", 100.0)

    set_if_needed("issued_date", "2026-01-01")
    set_if_needed("due_date", "2026-01-15")
    set_if_needed("period_start", "2026-01-01")
    set_if_needed("period_end", "2026-01-31")

    set_if_needed("from_date", "2026-01-01")
    set_if_needed("to_date", "2026-01-31")
    set_if_needed("from", "2026-01-01")
    set_if_needed("to", "2026-01-31")

    missing = [k for k in required if k not in payload]
    if missing:
        raise AssertionError(
            f"OpenAPI required fields not satisfied by test builder: {missing}. "
            f"Schema properties={list(props.keys())}"
        )

    return payload

def _ensure_customer_and_property(client):
    r_c = client.get("/api/v1/customers")
    assert r_c.status_code == 200
    customers = r_c.json()
    if not customers:
        pytest.skip("No customers in DB; cannot test invoices write without at least 1 customer.")
    customer_id = customers[0]["customer_id"]

    r_p = client.get("/api/v1/properties")
    assert r_p.status_code == 200
    props = r_p.json()

    prop = next((p for p in props if p["customer_id"] == customer_id), None)
    if prop:
        return customer_id, prop["property_id"]

    payload_prop = {
        "customer_id": customer_id,
        "label": "Invoice Test Property",
        "address1": "1 Test St",
        "city": "Rincon",
        "state": "PR",
        "postal_code": "00677",
        "is_active": 1,
    }
    r_new = client.post("/api/v1/properties", json=payload_prop)
    assert r_new.status_code in (200, 201)
    body = r_new.json()
    return customer_id, body["property_id"]


def _ensure_two_customers_with_distinct_properties(client):
    """
    Necesario para probar 'property no pertenece al customer'.
    Si no hay suficiente data, crea lo mínimo.
    """
    r_c = client.get("/api/v1/customers")
    assert r_c.status_code == 200
    customers = r_c.json()
    if len(customers) < 2:
        r_new = client.post("/api/v1/customers", json={"first_name": "Test", "last_name": "Customer2"})
        assert r_new.status_code in (200, 201)
        customers = client.get("/api/v1/customers").json()

    c1 = customers[0]["customer_id"]
    c2 = customers[1]["customer_id"]

    r_p = client.get("/api/v1/properties")
    assert r_p.status_code == 200
    props = r_p.json()

    p1 = next((p for p in props if p["customer_id"] == c1), None)
    p2 = next((p for p in props if p["customer_id"] == c2), None)

    def create_prop(cid: int, label: str):
        r = client.post(
            "/api/v1/properties",
            json={
                "customer_id": cid,
                "label": label,
                "address1": "2 Test St",
                "city": "Rincon",
                "state": "PR",
                "postal_code": "00677",
                "is_active": 1,
            },
        )
        assert r.status_code in (200, 201)
        return r.json()["property_id"]

    if not p1:
        p1_id = create_prop(c1, "Prop C1")
    else:
        p1_id = p1["property_id"]

    if not p2:
        p2_id = create_prop(c2, "Prop C2")
    else:
        p2_id = p2["property_id"]

    return c1, p1_id, c2, p2_id


def test_create_invoice_ok(client):
    spec = _openapi(client)
    schema = _schema_for_post_invoices(spec)

    customer_id, property_id = _ensure_customer_and_property(client)

    base = {"customer_id": customer_id, "property_id": property_id}
    payload = _pick_minimal_payload_from_schema(schema, base)

    r = client.post("/api/v1/invoices", json=payload)
    assert r.status_code in (200, 201)
    assert _has_request_id_header(r.headers)

    body = r.json()
    assert "invoice_id" in body


def test_create_invoice_validation_error_422_standard_shape(client):
    r = client.post("/api/v1/invoices", json={})
    assert r.status_code == 422

    body = r.json()
    assert body["code"] == "REQUEST_VALIDATION_ERROR"
    assert body["message"] == "Invalid request"
    assert "errors" in body["details"]
    assert "request_id" in body["details"]
    assert "timestamp" in body


def test_create_invoice_property_not_belong_to_customer_fails_with_standard_error_shape(client):
    spec = _openapi(client)
    schema = _schema_for_post_invoices(spec)

    c1, p1, c2, p2 = _ensure_two_customers_with_distinct_properties(client)

    base = {"customer_id": c1, "property_id": p2}
    payload = _pick_minimal_payload_from_schema(schema, base)

    r = client.post("/api/v1/invoices", json=payload)

    assert r.status_code in (400, 404, 409)

    body = r.json()
    _assert_standard_error_shape(body)
