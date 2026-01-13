import pytest


def _has_request_id_header(headers) -> bool:
    return "x-request-id" in {k.lower(): v for k, v in headers.items()}


def test_list_properties_returns_list_and_request_id_header(client):
    r = client.get("/api/v1/properties")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert _has_request_id_header(r.headers)


def test_get_property_404_uses_standard_error_shape(client):
    r = client.get("/api/v1/properties/999999")

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
