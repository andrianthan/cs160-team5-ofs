from flask import request
from datetime import datetime, timezone
from .models.robot import Robot as RobotModel
from .models.trip import Trip
from .models.trip_stop import TripStop
from .config import Config
from .extensions import db

# AVAILABLE -(trip assigned)-> LOADING
# AVAILABLE -(manual override/low battery)-> OFFLINE
# LOADING -(loading complete)-> OUT_FOR_DELIVERY
# LOADING -(trip canceled)-> AVAILABLE
# OUT_FOR_DELIVERY -(last stop)-> RETURNING
# RETURNING -(depot reached)-> AVAILABLE
# OFFLINE -(maintenance resolved)-> AVAILABLE
# ANY -(critical failure)-> OFFLINE
# AVAILABLE -(last bot in depot)-> RESERVED
# RESERVED -(multiple bots in depot)-> AVAILABLE
# RESERVED -(manager approved trip)-> LOADING
#robot states
AVAILABLE = "available"
RESERVED = "reserved"
LOADING = "loading"
OUT_FOR_DELIVERY = "out_for_delivery"
RETURNING = "returning"
OFFLINE = "offline"
# TODO: use actual coordinates of the store
STORE_LAT = 0.0
STORE_LONG = 0.0
# for battery; not outlined in doc, implementation optional (maybe?)
'''
MAX_BAT = 100.0
LOW_BAT = 20.0
MIN_BAT = 0.0
'''

class Robot():
    #robot transitions
    TRANSITIONS = {
        AVAILABLE: {
            "trip_assigned": LOADING,
            "manual_override": OFFLINE,
            "last_bot": RESERVED,
            "critical_failure": OFFLINE
        },
        RESERVED: {
            "multiple_bots": AVAILABLE, # remove?
            "trip_assigned": LOADING,
            "critical_failure": OFFLINE
        },
        LOADING: {
            "loading_complete": OUT_FOR_DELIVERY,
            "trip_canceled": AVAILABLE,
            "critical_failure": OFFLINE
        },
        OUT_FOR_DELIVERY: {
            "last_stop": RETURNING,
            "critical_failure": OFFLINE
        },
        RETURNING: {
            "depot_reached": AVAILABLE,
            "critical_failure": OFFLINE
        },
        OFFLINE: {
            "maintenance_resolved": AVAILABLE,
        }
    }

    def __init__(self, id, robot_code):
        self.id = id
        bot = db.session.get(RobotModel, id)
        if bot:
            self.code = bot.robot_code
            self.state = bot.status
            self.latitude = bot.current_latitude
            self.longitude = bot.current_longitude
        else: 
            self.code = robot_code
            self.state = AVAILABLE
            self.latitude = STORE_LAT
            self.longitude = STORE_LONG
            bot = RobotModel()
            bot.id = self.id
            bot.robot_code = self.code
            bot.status = self.state
            bot.current_latitude = self.latitude
            bot.current_longitude = self.longitude
            bot.updated_at = datetime.now(timezone.utc)
            db.session.add(bot)
            db.session.commit()
        #self.battery = MAX_BAT
        self.bot = bot #model

    #for updating location - can combine to return x,y instead - delete if redundant
    def get_current_lat(self):
        return self.latitude
    #this one too
    def get_current_long(self):
        return self.longitude

    # TODO: simulate robot movement on given route
    # if using same 
    def do_trip(self, trip:Trip):
        if not self.trigger("trip_assigned"):
            print(f"loading failed; robot not available; current state = {self.state}")
            return
        #loading time
        self.load_bot()
        if not self.trigger("loading_complete"):
            print(f"dispatch failed; robot not in loading state; current state = {self.state}")
            return
        route_geoemetry = trip.route_geometry
        trip.robot = self.bot
        stops = trip.stops
        for trip_stop in stops:
            self.travel(trip_stop)
            #wait for unloading before moving on to next stop

        #at last stop:
        self.trigger("last_stop")
        #trip over:
        trip.completed_at = datetime.now(timezone.utc)
        #return home
        self.trigger("depot_reached")
        return

    def travel(self, stop:TripStop):
        #travel start
        #TODO: implement travel

        #destination reached
        stop.arrived_at = datetime.now(timezone.utc)
        stop.completed_at = datetime.now(timezone.utc)
        return

    #for taking bot offline
    def manual_override(self):
        if not self.trigger("manual_override"):
            print(f"manual override failed; robot not available; current state = {self.state}")
        return
    def critical_failure(self):
        if not self.trigger("critical_failure"):
            print(f"critical failure: already offline or invalid state; current state = {self.state}")
        print(f"GET THIS ROBOT {self.latitude},{self.longitude}")
        return
    #for designating bots as reserved or available
    def reserve_bot():
        #TODO: check if reserved bot exists, then check if available exists, if yes reserve
        return
    # reserved to available unnecessary?

    #for loading robot
    def load_bot(self):
        #probably just wait? also prompt continue or cancel trip
        return

    #for resolve maintenance
    def resolve_maintenance(self):
        return
    
    # TODO: state transitions
    def trigger(self, event:str):
        if event in self.TRANSITIONS[self.state]:
            next_state = self.TRANSITIONS[self.state][event]
            # TODO: change to proper notification to employee/manager, customer if appropriate
            self.bot.status = next_state
            self.bot.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            print(f"Transitioning: {self.state} -> {next_state} (Event: {event})")
            self.state = next_state
            return True
        else:
            print(f"Ignored event '{event}' while in {self.state}")
            return False
