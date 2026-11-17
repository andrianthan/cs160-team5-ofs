import pytest

from app import routing
from app.extensions import db
from app.models import Trip

from test_trips import CITY_HALL, NEAR_CITY_HALL, make_order, make_user, prepare, staff  # noqa: F401


@pytest.fixture(autouse=True)
def no_mapbox(app):
    app.config["MAPBOX_ACCESS_TOKEN"] = None  # never hit the real API from tests


class FakeResp:
    def __init__(self, status, data):
        self.status_code, self._data = status, data

    def json(self):
        return self._data


def build_trip(client, staff, points):
    trip_id = None
    for p in points:
        trip_id = prepare(client, make_order(staff, p))["id"]
    return db.session.get(Trip, trip_id)


def test_fallback_orders_nearest_first_and_sets_route(app, client, staff):
    app.config["STORE_LAT"], app.config["STORE_LNG"] = 37.3340, -121.8858  # just south of City Hall
    far_first = [(37.3404, -121.8858), (37.3377, -121.8858)]  # farther one placed first
    trip = build_trip(client, staff, far_first)
    routing.optimize_route(trip)
    db.session.commit()
    assert [(float(s.latitude), s.stop_number) for s in trip.stops] == [(37.3377, 1), (37.3404, 2)]
    assert trip.route_geometry["type"] == "LineString"
    assert len(trip.route_geometry["coordinates"]) == 4  # depot, 2 stops, depot
    assert trip.estimated_duration_minutes >= 1
    assert trip.stops[0].estimated_arrival < trip.stops[1].estimated_arrival


def test_optimize_is_idempotent(app, client, staff):
    trip = build_trip(client, staff, [CITY_HALL, NEAR_CITY_HALL])
    routing.optimize_route(trip)
    db.session.commit()
    ids = [s.id for s in trip.stops]
    routing.optimize_route(trip)
    db.session.commit()
    assert [s.id for s in trip.stops] == ids


def test_mapbox_order_is_used_when_token_set(app, client, staff, monkeypatch):
    app.config["MAPBOX_ACCESS_TOKEN"] = "tok"
    trip = build_trip(client, staff, [CITY_HALL, NEAR_CITY_HALL])
    first, second = trip.orders[0], trip.orders[1]
    seen = {}

    def fake_get(url, params, timeout):
        seen["url"] = url
        # Mapbox says: depot, then input #2, then input #1
        return FakeResp(200, {
            "code": "Ok",
            "waypoints": [{"waypoint_index": 0}, {"waypoint_index": 2}, {"waypoint_index": 1}],
            "trips": [{"legs": [{"duration": 60}, {"duration": 30}, {"duration": 90}],
                       "geometry": {"coordinates": [[1, 2], [3, 4]]}}],
        })

    monkeypatch.setattr(routing.requests, "get", fake_get)
    routing.optimize_route(trip)
    db.session.commit()
    assert "optimized-trips" in seen["url"]
    assert [s.order_id for s in trip.stops] == [second.id, first.id]
    assert trip.route_geometry["coordinates"] == [[1, 2], [3, 4]]
    assert trip.estimated_duration_minutes == 3


@pytest.mark.parametrize("failure", ["http", "raise"])
def test_mapbox_failure_falls_back(app, client, staff, monkeypatch, failure):
    app.config["MAPBOX_ACCESS_TOKEN"] = "tok"
    trip = build_trip(client, staff, [CITY_HALL, NEAR_CITY_HALL])

    def fake_get(url, params, timeout):
        if failure == "raise":
            raise routing.requests.ConnectionError("down")
        return FakeResp(422, {"code": "InvalidInput", "message": "bad"})

    monkeypatch.setattr(routing.requests, "get", fake_get)
    routing.optimize_route(trip)
    db.session.commit()
    assert len(trip.stops) == 2 and trip.route_geometry["type"] == "LineString"
