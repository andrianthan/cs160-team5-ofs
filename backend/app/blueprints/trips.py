# T13 — Delivery Planning and trip grouping. Owner: Notario Ethan Rodriguez.
# LLD 3: trip grouping loop (oldest Order first, nearest neighbors, BR-2/BR-6),
# 30-min dispatch timer (BR-7). T14 Route Optimizer (Mapbox Optimization) and
# T15 Robot Fleet simulator feed into these same endpoints.
from flask import Blueprint, current_app, jsonify, request

import uuid # FOR PLACEHOLDER ORDER OBJECT - REMOVE IF UNUSED IN FINAL
from datetime import datetime, timedelta

bp = Blueprint("trips", __name__, url_prefix="/api/trips")

# PLACEHOLDER ORDER OBJECT - ADJUST IMPLEMENTATION WHEN READY
class Order:
    def __init__(self, address, weight, time):
        self.id = uuid.uuid4()
        self.address = address #mapbox location
        self.weight = weight #pounds
        self.time = time #datetime

MAX_ORDERS = 10
MAX_WEIGHT = 200.0
order_queue = [] #placeholder, orders added in order of time

@bp.get("")
def list_trips():
    if len(order_queue) == 0:
        return None
    seed_order = order_queue[0]
    trip = [] #can try min heap implementation; parse through order queue for now
    trip.add(seed_order)
    order_queue.remove(seed_order)
    order_count = 1
    current_weight = seed_order.weight
    seed_address = seed_order.address

    #Mapbox directions/distance
    token = current_app.config.get("MAPBOX_ACCESS_TOKEN")
    if not token:
        current_app.logger.warning("MAPBOX_ACCESS_TOKEN not set — directions disabled")
        return None

    profile = "walking" #seems to be most appropriate profile - adjust if needed

    while order_count < MAX_ORDERS:
        nearest = None
        shortest_distance = 1000.0 #this max value should be well out of range
        
        for candidate in order_queue:
            if (current_weight + candidate.weight <= MAX_WEIGHT):
                #mapbox to calculate distance between points
                coordinates = seed_address + ";" + candidate.address #for this, address stored as string "x,y"
                url = f"https://api.mapbox.com/directions-matrix/v1/mapbox/{profile}/{coordinates}"
                params = {
                    "annotations": "distance,duration", # Returns both distance and time
                    "access_token": token
                }
                #time potentially more useful; keeping it commented out for now

                response = request.get(url, params=params)
                data = response.json()

                if response.status_code == 200:
                    # 'distances' contains a 2D matrix of results in meters
                    # From coordinates[0] to coordinates[1]:
                    distance_meters = data["distances"][0][1] 
                    #duration_seconds = data["durations"][0][1]
                      
                    #print(f"Distance: {distance_meters / 1000:.2f} km")
                    #print(f"Travel Time: {duration_seconds / 60:.1f} minutes")
                else:
                    print("Error:", data.get("message"))
                if distance_meters < shortest_distance:
                    shortest_distance = distance_meters
                    nearest = candidate
        if nearest is None: # no more valid candidates
            break
        trip.add(nearest)
        order_queue.remove(nearest)
        order_count += 1
        current_weight += nearest.weight
        seed_address = nearest.address #calculate distance from newest address

    #return trip
    #1 trip(list of destinations) or list of trips?
    return jsonify(error="not_implemented"), 501 #not full implementation, so keeping this for now


@bp.post("/<trip_id>/dispatch")
def dispatch_trip(trip_id):
    return jsonify(error="not_implemented"), 501
