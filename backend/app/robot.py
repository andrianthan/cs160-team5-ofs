from flask import request
from datetime import datetime, timezone, timedelta
from .models.robot import Robot as RobotModel
from .models.trip import Trip
from .models.trip_stop import TripStop
from .config import Config
from .extensions import db
from .planning import distance_km #haversine distance

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

# TODO: use actual coordinates of the store, using coords of duncan hall as placeholder:
# 37.332339712229526, -121.88183268335278
STORE_LAT = 37.332339712229526
STORE_LONG = -121.88183268335278

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

    # TODO: request a robot to do a trip (dispatch) - probably remove do_trip() and travel()
    def dispatch_trip(trip:Trip, status=AVAILABLE):
        # search db for available robot, or reserved if specified
        # if none, notify
        # Mapbox Optimization call - gives distance(meters), duration(seconds), geometry
        # update Trip dispatched_at = now, estimated_duration = now + duration, geometry = geometry
        # for each order in trip.orders and each stop in trip.stops:
        # increment simulated_timer(starting from now) by this leg's estimated duration, set arrival and completion to timer value
        # have robot under OUT_FOR_DELIVERY state until estimated completed time
        # can do this incremented timer OR actually wait or sleep for duration, then update in real time
        return

    # can be separate from delivery route
    def return_home(self):
        #call mapbox route optimization
        #for duration, RETURNING
        #or try to simulate live travel and depot_reached upon arrival home
        return
    
    # TODO: simulate robot movement on given route
    # if using same route in my old T14 mapbox api call, should be round trip
    def do_trip(self, trip:Trip):
        if not self.trigger("trip_assigned"):
            print(f"loading failed; robot not available; current state = {self.state}")
            return
        self.reserve_bot()#if trip assigned, might be reserved, try to reserve new bot
        #loading time
        self.load_bot()
        if not self.trigger("loading_complete"):
            print(f"dispatch failed; robot not in loading state; current state = {self.state}")
            return
        
        route_geoemetry = trip.route_geometry
        # Mapbox route geometry (assuming standard GeoJSON formatting)
        # e.g., {'type': 'LineString', 'coordinates': [[lon1, lat1], [lon2, lat2], ...]}
        route_coords = route_geoemetry.get("coordinates", []) if isinstance(route_geoemetry, dict) else route_geoemetry
        
        trip.robot = self.bot
        stops = trip.stops #should already be ordered by stop number
        time_elapsed_seconds = 0.0
        
        current_stop_idx = 0

        # Simulate moving along the route coordinates
        for coord in route_coords:
            # Mapbox returns [longitude, latitude]
            self.longitude = coord[0] 
            self.latitude = coord[1]
            
            # Update DB Model
            self.bot.current_longitude = self.longitude
            self.bot.current_latitude = self.latitude
            self.bot.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            
            # Simulate time passing between nodes (adjust based on desired simulation speed)
            #time.sleep(1) 
            time_elapsed_seconds+=1 #should be duration of stop -> stop
            # can get durations from mapbox optimization call but not from trip or trip stop model objects
            #timer needs to be non-blocking - using counter for now
            
            # Check if we are close to the next stop (e.g., within 15 meters)
            if current_stop_idx < len(stops):
                target_stop = stops[current_stop_idx]
                distance = distance_km(
                    self.longitude, self.latitude, 
                    target_stop.longitude, target_stop.latitude
                )
                
                if distance < 15.0: 
                    self.travel(target_stop)
                    current_stop_idx += 1

        #at last stop:
        self.trigger("last_stop")
        #trip over:
        trip.completed_at = datetime.now(timezone.utc)
        #return home
        self.trigger("depot_reached")
        self.reserve_bot()#returning to available state, so reserve if none currently reserve
        return

    def travel(self, stop:TripStop):
        # Destination reached
        print(f"Arrived at stop {stop.id}. Unloading...")
        stop.arrived_at = datetime.now(timezone.utc)

        #unloading time
        
        stop.completed_at = datetime.now(timezone.utc)
        db.session.commit()
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
        #check if reserved bot exists, then check if available exists, if yes reserve
        reserved_bot = db.session.query(RobotModel).filter_by(status = RESERVED).first()
        if  reserved_bot is not None:
            print(f"Robot with ID {reserved_bot.id} is already reserved")
            return
        reserved_bot = db.session.query(RobotModel).filter_by(status = AVAILABLE).first()
        if reserved_bot is not None:
            reserved_bot.status = RESERVED
            print(f"Robot with ID {reserved_bot.id} has been reserved")
            return
        print("No robots currently available to reserve")
        return
    # reserved to available unnecessary?

    #for loading robot
    def load_bot(self):
        #probably just wait? also prompt continue or cancel trip
        answer = ""
        #TODO: replace with button for employee/manager page
        while answer not in ("Continue", "Cancel"):
            answer = input("Press Continue to finish loading and dispatch or Cancel to cancel loading and free up this robot")
        if answer == "Cancel":
            self.trigger("trip_canceled")
            print(f"Trip canceled; Robot with ID {self.id} now available")
            self.reserve_bot()#returning to available state, so reserve if none currently reserved
        return

    #for resolve maintenance
    def resolve_maintenance(self):
        self.reserve_bot()#returning to available state, so reserve if none currently reserved
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
