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


# ---- "Next stop" button: stepping a Trip by hand ----

def dispatch_paused(app, client, staff, *places):
    """Dispatch a Trip with the auto-drive off, so it stays out for delivery for the Next stop button."""
    app.config["ROBOT_SIM_ENABLED"] = False
    orders = [make_order(staff, at) for at in places]
    trip_id = None
    for o in orders:
        trip_id = prepare(client, o)["id"]
    assert client.post(f"/api/trips/{trip_id}/dispatch").status_code == 200
    return trip_id


def test_next_stop_delivers_one_stop_at_a_time_then_returns(app, client, staff):
    add_robots(2)
    trip_id = dispatch_paused(app, client, staff, CITY_HALL, NEAR_CITY_HALL)

    body = client.post(f"/api/trips/{trip_id}/advance").get_json()
    assert body["step"] == "delivered" and body["stopNumber"] == 1
    first, second = body["stops"]
    assert first["status"] == "delivered" and second["status"] != "delivered"
    robot = db.session.get(RobotModel, body["robotId"])
    assert (float(robot.current_latitude), float(robot.current_longitude)) == (first["lat"], first["lng"])
    assert robot.status == "out_for_delivery"

    body = client.post(f"/api/trips/{trip_id}/advance").get_json()
    assert body["step"] == "delivered" and body["stopNumber"] == 2 and body["status"] == "dispatched"

    body = client.post(f"/api/trips/{trip_id}/advance").get_json()  # every stop done: back to the store
    assert body["step"] == "returned" and body["status"] == "completed"
    trip = db.session.get(Trip, trip_id)
    assert all(s.arrived_at and s.completed_at for s in trip.stops)
    assert all(o.status == DELIVERED for o in trip.orders)
    robot = db.session.get(RobotModel, trip.robot_id)
    assert robot.status == "available"
    assert (float(robot.current_latitude), float(robot.current_longitude)) == (app.config["STORE_LAT"], app.config["STORE_LNG"])

    assert client.post(f"/api/trips/{trip_id}/advance").status_code == 409  # completed: nothing left


def test_next_stop_only_for_dispatched_trips_and_staff(app, client, staff):
    add_robots(1)
    trip_id = prepare(client, make_order(staff))["id"]
    resp = client.post(f"/api/trips/{trip_id}/advance")
    assert resp.status_code == 409 and resp.get_json()["error"] == "invalid_transition"
    assert client.post("/api/trips/999/advance").status_code == 404
    client.post("/api/auth/logout")
    assert client.post(f"/api/trips/{trip_id}/advance").status_code == 401


def test_next_stop_refused_when_robot_went_offline(app, client, staff):
    add_robots(1)
    trip_id = dispatch_paused(app, client, staff, CITY_HALL)
    trip = db.session.get(Trip, trip_id)
    Robot.get(trip.robot_id).critical_failure()
    resp = client.post(f"/api/trips/{trip_id}/advance")
    assert resp.status_code == 409 and "offline" in resp.get_json()["message"]


def test_auto_drive_stops_once_a_trip_is_taken_over(app, client, staff):
    from app import robot as fleet

    add_robots(1)
    trip_id = dispatch_paused(app, client, staff, CITY_HALL, NEAR_CITY_HALL)
    client.post(f"/api/trips/{trip_id}/advance")  # stop 1 by hand
    fleet.run_trip(trip_id)  # what the background thread would do next: it must leave the Trip alone
    trip = db.session.get(Trip, trip_id)
    assert [s.status for s in trip.stops][1] != "delivered" and trip.status == "dispatched"
    fleet._manual.discard(trip_id)


# ---- adding and removing Robots (Managers only) ----

def login_manager(client):
    manager = make_user("boss@example.com", "manager")
    client.post("/api/auth/logout")
    assert client.post("/api/auth/login", json={"email": manager.email, "password": PASSWORD}).status_code == 200


def test_manager_adds_robots_with_the_next_code_at_the_store(app, client, staff):
    login_manager(client)
    db.session.add(RobotModel(robot_code="OFS-R3", status="available"))
    db.session.commit()
    resp = client.post("/api/robots")
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["code"] == "OFS-R4" and body["status"] == "available"
    assert (body["lat"], body["lng"]) == (app.config["STORE_LAT"], app.config["STORE_LNG"])
    assert client.post("/api/robots").get_json()["code"] == "OFS-R5"
    assert {m.status for m in RobotModel.query.all()} == {"available"}  # more than one home: no reserve


def test_first_robot_added_is_the_reserve(app, client, staff):
    login_manager(client)
    assert client.post("/api/robots").get_json()["code"] == "OFS-R1"
    assert RobotModel.query.one().status == "reserved"


def test_manager_removes_robot_in_depot_and_its_old_trips_survive(app, client, staff):
    add_robots(2)
    order = make_order(staff)
    trip_id = prepare(client, order)["id"]
    client.post(f"/api/trips/{trip_id}/dispatch")  # runs inline to completion
    used = db.session.get(Trip, trip_id).robot_id

    login_manager(client)
    resp = client.delete(f"/api/robots/{used}")
    assert resp.status_code == 200 and resp.get_json()["removed"].startswith("R-")
    assert db.session.get(RobotModel, used) is None
    trip = db.session.get(Trip, trip_id)
    assert trip.status == COMPLETED and trip.robot_id is None
    assert RobotModel.query.one().status == "reserved"  # one left: it becomes the reserve
    assert client.get(f"/api/tracking/{order.id}").status_code == 200  # tracking still works without the Robot
    assert client.delete(f"/api/robots/{used}").status_code == 404


def test_robot_on_a_trip_cannot_be_removed(app, client, staff):
    add_robots(1)
    trip_id = dispatch_paused(app, client, staff, CITY_HALL)
    robot_id = db.session.get(Trip, trip_id).robot_id
    login_manager(client)
    resp = client.delete(f"/api/robots/{robot_id}")
    assert resp.status_code == 409 and "out for delivery" in resp.get_json()["message"]
    assert db.session.get(RobotModel, robot_id) is not None


def test_offline_robot_can_be_removed(app, client, staff):
    a, _ = add_robots(2)
    a.manual_override()
    login_manager(client)
    assert client.delete(f"/api/robots/{a.model.id}").status_code == 200


def test_employees_cannot_add_or_remove_robots(app, client, staff):
    (r,) = add_robots(1)
    assert client.post("/api/robots").status_code == 403
    assert client.delete(f"/api/robots/{r.model.id}").status_code == 403


def test_next_stop_rechecks_the_trip_under_the_lock(app, client, staff):
    """The auto-drive can finish a Trip between the endpoint's check and the step: nothing may move then."""
    from app import robot as fleet

    add_robots(1)
    trip_id = dispatch_paused(app, client, staff, CITY_HALL)
    trip = db.session.get(Trip, trip_id)
    trip.status = COMPLETED  # as if the auto-drive just completed it
    db.session.commit()
    robot = db.session.get(RobotModel, trip.robot_id)
    before = (robot.current_latitude, robot.current_longitude, robot.status)
    try:
        fleet.advance_trip(trip)
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "completed" in str(exc)
    robot = db.session.get(RobotModel, trip.robot_id)
    assert (robot.current_latitude, robot.current_longitude, robot.status) == before


def test_add_robot_retries_when_two_managers_pick_the_same_code(app, client, staff, monkeypatch):
    from app.blueprints import robots as robots_bp

    login_manager(client)
    db.session.add(RobotModel(robot_code="OFS-R1", status="available"))
    db.session.commit()
    codes = iter(["OFS-R1", "OFS-R2"])  # the first pick collides, as if another Manager just took it
    monkeypatch.setattr(robots_bp, "next_robot_code", lambda: next(codes))
    resp = client.post("/api/robots")
    assert resp.status_code == 201 and resp.get_json()["code"] == "OFS-R2"


def test_robot_codes_skip_other_names_and_gaps(app):
    from app.robot import next_robot_code

    for code in ("OFS-R2", "OFS-R7", "ROBOT-09", "OFS-Rx", "R-1"):
        db.session.add(RobotModel(robot_code=code, status="available"))
    db.session.commit()
    assert next_robot_code() == "OFS-R8"
