# T15 — Simulated robot fleet. Owner: Notario Ethan Rodriguez.
# A Robot's life is a small state machine (below). run_trip() plays a dispatched Trip: the Robot
# drives to each stop in order, hands over the Order (Delivered + customer email), then drives back
# to the store. Positions are written to the robots table every tick so tracking (T16) can read them.
#
#   available --trip_assigned--> loading --loading_complete--> out_for_delivery
#   out_for_delivery --last_stop--> returning --depot_reached--> available
#   loading --trip_canceled--> available;  available --manual_override--> offline
#   any --critical_failure--> offline;  offline --maintenance_resolved--> available
#   available --last_bot--> reserved (the one Robot always kept in the depot)
#   reserved --multiple_bots--> available;  reserved --trip_assigned--> loading
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone

from flask import current_app

from . import notifications
from .extensions import db
from .models import Order, Trip
from .models.order import DELIVERED
from .models.robot import Robot as RobotModel
from .models.trip import COMPLETED, DISPATCHED

AVAILABLE = "available"
RESERVED = "reserved"
LOADING = "loading"
OUT_FOR_DELIVERY = "out_for_delivery"
RETURNING = "returning"
OFFLINE = "offline"
IN_DEPOT = (AVAILABLE, RESERVED)

# Every Robot is named OFS-R1, OFS-R2, ... (the seed, the demo data and the Dispatch page's "Add robot").
CODE_PREFIX = "OFS-R"


def robot_code(n):
    return f"{CODE_PREFIX}{n}"


def next_robot_code():
    """One past the highest OFS-R number in use (gaps left by removed Robots are not reused)."""
    numbers = [int(code[len(CODE_PREFIX):]) for (code,) in db.session.query(RobotModel.robot_code)
               if code.startswith(CODE_PREFIX) and code[len(CODE_PREFIX):].isdigit()]
    return robot_code(max(numbers, default=0) + 1)

TRANSITIONS = {
    AVAILABLE: {"trip_assigned": LOADING, "manual_override": OFFLINE, "last_bot": RESERVED,
                "critical_failure": OFFLINE},
    RESERVED: {"multiple_bots": AVAILABLE, "trip_assigned": LOADING, "manual_override": OFFLINE,
               "critical_failure": OFFLINE},
    LOADING: {"loading_complete": OUT_FOR_DELIVERY, "trip_canceled": AVAILABLE, "critical_failure": OFFLINE},
    OUT_FOR_DELIVERY: {"last_stop": RETURNING, "critical_failure": OFFLINE},
    RETURNING: {"depot_reached": AVAILABLE, "critical_failure": OFFLINE},
    OFFLINE: {"maintenance_resolved": AVAILABLE},
}


def _now():
    return datetime.now(timezone.utc)


class Robot:
    """State-machine wrapper around one robots row. Commits on every transition / move."""

    def __init__(self, model):
        self.model = model

    @classmethod
    def get(cls, robot_id):
        model = db.session.get(RobotModel, robot_id)
        return cls(model) if model else None

    @classmethod
    def create(cls, code):
        lat, lng = current_app.config["STORE_LAT"], current_app.config["STORE_LNG"]
        model = RobotModel(robot_code=code, status=AVAILABLE, current_latitude=lat, current_longitude=lng)
        db.session.add(model)
        db.session.flush()
        return cls(model)

    @property
    def state(self):
        return self.model.status

    @property
    def position(self):
        return float(self.model.current_latitude), float(self.model.current_longitude)

    def trigger(self, event):
        """Apply an event. Returns False (and changes nothing) if it isn't valid in this state."""
        nxt = TRANSITIONS[self.state].get(event)
        if nxt is None:
            current_app.logger.info("Robot %s ignored %r while %s", self.model.robot_code, event, self.state)
            return False
        self.model.status = nxt
        self.model.updated_at = _now()
        db.session.commit()
        return True

    def move_to(self, lat, lng):
        self.model.current_latitude, self.model.current_longitude = lat, lng
        self.model.updated_at = _now()
        db.session.commit()

    def manual_override(self):
        ok = self.trigger("manual_override")
        rebalance_reserve()  # the depot may now have a single Robot left
        return ok

    def critical_failure(self):
        return self.trigger("critical_failure")

    def resolve_maintenance(self):
        ok = self.trigger("maintenance_resolved")
        rebalance_reserve()
        return ok


def pick_robot():
    """A Robot in the depot for the next Trip: a free one first, the reserve only as a last resort."""
    for status in (AVAILABLE, RESERVED):
        model = RobotModel.query.filter_by(status=status).order_by(RobotModel.id).first()
        if model:
            return Robot(model)
    return None


def rebalance_reserve():
    """Keep exactly one Robot reserved when only one is left in the depot; release it otherwise."""
    depot = RobotModel.query.filter(RobotModel.status.in_(IN_DEPOT)).order_by(RobotModel.id).all()
    if len(depot) == 1 and depot[0].status == AVAILABLE:
        Robot(depot[0]).trigger("last_bot")
    elif len(depot) > 1:
        for model in depot:
            if model.status == RESERVED:
                Robot(model).trigger("multiple_bots")


def start_trip(robot, trip):
    """Assign the Robot and finish loading (the Employee's Dispatch click is the loading confirmation)."""
    if not robot.trigger("trip_assigned"):
        return False
    trip.robot_id = robot.model.id
    robot.move_to(current_app.config["STORE_LAT"], current_app.config["STORE_LNG"])
    return robot.trigger("loading_complete")


def launch(trip_id):
    """Play the Trip in the background, or inline when ROBOT_SIM_ASYNC is off (tests)."""
    app = current_app._get_current_object()
    if not app.config["ROBOT_SIM_ENABLED"]:
        return
    if app.config["ROBOT_SIM_ASYNC"]:
        threading.Thread(target=_in_context, args=(app, trip_id), daemon=True).start()
    else:
        run_trip(trip_id)


def _in_context(app, trip_id):
    with app.app_context():
        try:
            run_trip(trip_id)
        except Exception:
            current_app.logger.exception("Robot simulation for trip %s crashed", trip_id)
            db.session.rollback()


# Trips an Employee is stepping through by hand (Dispatch page "Next stop"). The auto-drive thread checks
# this under the lock before every write and stops once its Trip is in here, so the two never both move a Robot.
# In-process only: fine for the one gunicorn worker the Docker setup runs.
_manual = set()
_lock = threading.Lock()


@contextmanager
def _turn(trip_id=None):
    """Hold the lock; yields False when an Employee has taken this Trip over. Ends this thread's open
    read transaction first: on SQLite an idle reader waiting here would block the lock holder's commit."""
    db.session.commit()
    with _lock:
        yield trip_id not in _manual


def _drive(robot, dest, trip_id):
    """Straight-line interpolation from the current position to dest in ROBOT_SIM_STEPS updates.
    Returns False if an Employee took the Trip over on the way."""
    cfg = current_app.config
    steps = max(1, cfg["ROBOT_SIM_STEPS"])
    lat0, lng0 = robot.position
    for i in range(1, steps + 1):
        f = i / steps
        with _turn(trip_id) as ours:
            if not ours:
                return False
            robot.move_to(lat0 + (dest[0] - lat0) * f, lng0 + (dest[1] - lng0) * f)
        if cfg["ROBOT_SIM_TICK_S"]:
            time.sleep(cfg["ROBOT_SIM_TICK_S"])
    return True


def _deliver(stop, now):
    """Hand over the Order at this stop. The caller commits and then notifies the customer."""
    stop.status, stop.completed_at = "delivered", now
    stop.arrived_at = stop.arrived_at or now
    order = db.session.get(Order, stop.order_id)
    order.status = DELIVERED
    return order


def _finish(robot, trip):
    """Back at the store: the Robot rejoins the depot and the Trip is completed."""
    robot.trigger("depot_reached")
    trip.status, trip.completed_at = COMPLETED, _now()
    db.session.commit()
    _manual.discard(trip.id)


def run_trip(trip_id):
    """Drive a dispatched Trip to completion: every stop in order, then home."""
    cfg = current_app.config
    trip = db.session.get(Trip, trip_id)
    robot = Robot.get(trip.robot_id) if trip and trip.robot_id else None
    if robot is None or robot.state != OUT_FOR_DELIVERY:
        return
    for stop in list(trip.stops):
        if robot.state != OUT_FOR_DELIVERY:  # went offline mid-trip: stop where it is
            return
        if stop.status == "delivered":
            continue
        if not _drive(robot, (float(stop.latitude), float(stop.longitude)), trip_id):
            return
        with _turn(trip_id) as ours:
            if not ours:
                return
            stop.status, stop.arrived_at = "arrived", _now()
            db.session.commit()
        if cfg["ROBOT_SIM_DWELL_S"]:
            time.sleep(cfg["ROBOT_SIM_DWELL_S"])
        with _turn(trip_id) as ours:
            if not ours:
                return
            order = _deliver(stop, _now())
            db.session.commit()
        notifications.notify_status_change(order)

    with _turn(trip_id) as ours:
        if not ours:
            return
        robot.trigger("last_stop")
    if not _drive(robot, (cfg["STORE_LAT"], cfg["STORE_LNG"]), trip_id):
        return
    with _turn(trip_id) as ours:
        if not ours:
            return
        _finish(robot, trip)
    rebalance_reserve()


def advance_trip(trip):
    """One step by hand, for demos and for Trips whose auto-drive stopped (e.g. the backend restarted):
    jump to the next stop and hand over its Order, or, once every stop is delivered, return to the store
    and complete the Trip. The auto-drive stops for this Trip from the first step on.
    Returns ("delivered", stop) or ("returned", None); raises ValueError when there is nothing to do."""
    with _turn():
        # Re-read under the lock: the auto-drive may have finished this Trip since the caller looked,
        # and its Robot may already be out on a new one.
        if trip.status != DISPATCHED:
            raise ValueError(f"This trip is {trip.status}, not out for delivery.")
        robot = Robot.get(trip.robot_id) if trip.robot_id else None
        if robot is None:
            raise ValueError("This trip has no Robot.")
        if robot.state not in (OUT_FOR_DELIVERY, RETURNING):
            raise ValueError(f"{robot.model.robot_code} is {robot.state.replace('_', ' ')}, so it can't move on.")
        _manual.add(trip.id)
        stop = next((s for s in trip.stops if s.status != "delivered"), None)
        if stop is not None and robot.state == OUT_FOR_DELIVERY:
            robot.move_to(float(stop.latitude), float(stop.longitude))
            order = _deliver(stop, _now())
            db.session.commit()
            step = ("delivered", stop)
        else:
            if robot.state == OUT_FOR_DELIVERY:
                robot.trigger("last_stop")
            robot.move_to(current_app.config["STORE_LAT"], current_app.config["STORE_LNG"])
            _finish(robot, trip)
            order, step = None, ("returned", None)
    if order is not None:
        notifications.notify_status_change(order)
    else:
        rebalance_reserve()
    return step
