from unittest.mock import patch

from app.blueprints.addresses import inside_delivery_zone

INSIDE = {"lat": 37.3355, "lng": -121.8907, "place_name": "200 S Market St, San Jose, CA"}
OUTSIDE = {"lat": 37.3900, "lng": -121.9500, "place_name": "Somewhere far away, San Jose, CA"}


def test_inside_delivery_zone_true_for_downtown_point():
    assert inside_delivery_zone(INSIDE) is True


def test_inside_delivery_zone_false_for_point_outside():
    assert inside_delivery_zone(OUTSIDE) is False


def test_validate_rejects_empty_address(client):
    resp = client.post("/api/addresses/validate", json={"address": ""})
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "invalid_address"


def test_validate_rejects_missing_address_field(client):
    resp = client.post("/api/addresses/validate", json={})
    assert resp.status_code == 400


@patch("app.blueprints.addresses.geocode")
def test_validate_accepts_address_inside_zone(mock_geocode, client):
    mock_geocode.return_value = INSIDE

    resp = client.post("/api/addresses/validate", json={"address": "200 S Market St"})

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["valid"] is True
    assert body["lat"] == INSIDE["lat"]
    assert body["lng"] == INSIDE["lng"]


@patch("app.blueprints.addresses.geocode")
def test_validate_rejects_address_outside_zone(mock_geocode, client):
    mock_geocode.return_value = OUTSIDE

    resp = client.post("/api/addresses/validate", json={"address": "Somewhere far away"})

    assert resp.status_code == 422
    assert resp.get_json()["error"] == "OUTSIDE_DELIVERY_ZONE"


@patch("app.blueprints.addresses.geocode")
def test_validate_returns_404_when_geocode_finds_nothing(mock_geocode, client):
    mock_geocode.return_value = None

    resp = client.post("/api/addresses/validate", json={"address": "asdkfjaslkdjf"})

    assert resp.status_code == 404
    assert resp.get_json()["error"] == "ADDRESS_NOT_FOUND"
