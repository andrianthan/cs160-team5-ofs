from app.extensions import db
from app.models import Robot as RobotModel, Trip, TripStop
from app.models.order import DELIVERED, OUT_FOR_DELIVERY
from app.models.trip import COMPLETED
from app.robot import Robot, pick_robot, rebalance_reserve

from test_trips import CITY_HALL, NEAR_CITY_HALL, SAP_CENTER, PASSWORD, make_order, make_user, prepare, staff  # noqa: F401


def add_robots(n):
    robots = [Robot.create(f"R-{i}") for i in range(1, n + 1)]
    db.session.commit()
    return robots


def test_state_machine_happy_path_and_invalid_events(app):
    (r,) = add_robots(1)
    assert not r.trigger("depot_reached")  # not valid while available
    assert r.state == "available"
    for event, state in [("trip_assigned", "loading"), ("loading_complete", "out_for_delivery"),
                         ("last_stop", "returning"), ("depot_reached", "available")]:
        assert r.trigger(event) and r.state == state


def test_offline_only_leaves_through_maintenance(app):
    (r,) = add_robots(1)
    assert r.manual_override() and r.state == "offline"
    assert not r.trigger("trip_assigned")
    assert r.trigger("maintenance_resolved") and r.state == "available"


def test_critical_failure_from_any_working_state(app):
    (r,) = add_robots(1)
    r.trigger("trip_assigned")
    assert r.critical_failure() and r.state == "offline"


def test_reserve_kept_only_for_last_robot_in_depot(app):
    a, b = add_robots(2)
    rebalance_reserve()
    assert [m.status for m in RobotModel.query.order_by(RobotModel.id)] == ["available", "available"]
    a.trigger("trip_assigned")  # a leaves: b is the last one home
    rebalance_reserve()
    assert db.session.get(RobotModel, b.model.id).status == "reserved"
    a.trigger("loading_complete"); a.trigger("last_stop"); a.trigger("depot_reached")
    rebalance_reserve()  # two home again: reserve released
    assert {m.status for m in RobotModel.query.all()} == {"available"}


def test_pick_robot_prefers_available_over_reserved(app):
    a, b = add_robots(2)
    a.model.status = "reserved"
    db.session.commit()
    assert pick_robot().model.id == b.model.id


def test_dispatch_runs_trip_to_completion(app, client, staff):
    add_robots(2)
    first = make_order(staff, CITY_HALL)
    second = make_order(staff, NEAR_CITY_HALL)
    trip_id = prepare(client, first)["id"]
    assert prepare(client, second)["id"] == trip_id

    resp = client.post(f"/api/trips/{trip_id}/dispatch")
    assert resp.status_code == 200

    trip = db.session.get(Trip, trip_id)
    assert trip.status == COMPLETED and trip.completed_at is not None
    assert [s.stop_number for s in trip.stops] == [1, 2]
    assert all(s.status == "delivered" and s.arrived_at and s.completed_at for s in trip.stops)
    assert all(o.status == DELIVERED for o in trip.orders)
    # both robots home: the reserve is released
    assert [m.status for m in RobotModel.query.all()] == ["available", "available"]
    robot = db.session.get(RobotModel, trip.robot_id)
    assert (float(robot.current_latitude), float(robot.current_longitude)) == (app.config["STORE_LAT"], app.config["STORE_LNG"])


def test_dispatch_without_robot_is_409_and_changes_nothing(app, client, staff):
    trip_id = prepare(client, make_order(staff))["id"]
    resp = client.post(f"/api/trips/{trip_id}/dispatch")
    assert resp.status_code == 409 and resp.get_json()["error"] == "no_robot_available"
    trip = db.session.get(Trip, trip_id)
    assert trip.status != "dispatched" and not trip.stops
    assert all(o.status == "planned" for o in trip.orders)


def test_offline_robots_are_not_used(app, client, staff):
    (r,) = add_robots(1)
    r.manual_override()
    trip_id = prepare(client, make_order(staff))["id"]
    assert client.post(f"/api/trips/{trip_id}/dispatch").status_code == 409


def test_robots_endpoint_is_staff_only(app, client, staff):
    add_robots(2)
    body = client.get("/api/robots").get_json()
    assert [r["code"] for r in body["robots"]] == ["R-1", "R-2"]
    client.post("/api/auth/logout")
    assert client.get("/api/robots").status_code == 401


# ---- tracking sees the simulated robot ----

def test_tracking_shows_finished_trip_and_robot_home(app, client, staff):
    add_robots(1)
    order = make_order(staff, SAP_CENTER)
    trip_id = prepare(client, order)["id"]
    client.post(f"/api/trips/{trip_id}/dispatch")

    body = client.get(f"/api/tracking/{order.id}").get_json()  # logged in as employee
    assert body["status"] == "delivered" and body["tripId"] == trip_id
    assert body["trip"]["status"] == "completed" and body["trip"]["estimatedDurationMinutes"] >= 1
    assert body["robot"]["robotCode"] == "R-1"
    assert (body["robot"]["latitude"], body["robot"]["longitude"]) == (app.config["STORE_LAT"], app.config["STORE_LNG"])


# ---- offline / online controls ----

def test_take_robot_offline_and_back(app, client, staff):
    add_robots(3)
    resp = client.post("/api/robots/1/offline")
    assert resp.status_code == 200 and resp.get_json()["status"] == "offline"
    assert client.post("/api/robots/1/offline").status_code == 409  # already offline
    resp = client.post("/api/robots/1/online")
    assert resp.status_code == 200 and resp.get_json()["status"] == "available"
    assert client.post("/api/robots/1/online").status_code == 409  # not offline any more
    assert client.post("/api/robots/99/offline").status_code == 404


def test_robot_on_a_trip_cannot_be_pulled(app, client, staff):
    (r,) = add_robots(1)
    r.trigger("trip_assigned")
    assert client.post(f"/api/robots/{r.model.id}/offline").status_code == 409


def test_offline_robot_never_gets_a_trip_and_reserve_follows(app, client, staff):
    add_robots(2)
    client.post("/api/robots/1/offline")  # R-2 is now the last one in the depot
    assert db.session.get(RobotModel, 2).status == "reserved"
    trip_id = prepare(client, make_order(staff))["id"]
    assert client.post(f"/api/trips/{trip_id}/dispatch").status_code == 200  # reserve may still be sent
    assert db.session.get(RobotModel, 1).status == "offline"
