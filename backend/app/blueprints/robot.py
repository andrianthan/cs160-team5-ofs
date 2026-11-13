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
MAX_BAT = 100.0
LOW_BAT = 20.0
MIN_BAT = 0.0

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
            "multiple_bots": AVAILABLE,
            "approved_trip": LOADING,
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
        self.code = robot_code # TODO: change to id & code defined in model
        self.state = AVAILABLE
        self.latitude = STORE_LAT
        self.longitude = STORE_LONG
        self.battery = MAX_BAT

    #for updating location - can combine to return x,y instead - delete if redundant
    def get_current_lat(self):
        return self.latitude
    #this one too
    def get_current_long(self):
        return self.longitude

    # TODO: simulate robot movement on given route
    def move(self):
        return

    # TODO: state transitions
    def trigger(self, event:str):
        if event in self.TRANSITIONS[self.state]:
            next_state = self.TRANSITIONS[self.state][event]
            # TODO: change to proper notification to employee/manager, customer if appropriate
            print(f"Transitioning: {self.state} -> {next_state} (Event: {event})")
            self.state = next_state

        else:
            print(f"Ignored event '{event}' while in {self.state}")