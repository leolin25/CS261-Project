import random
from django.utils import timezone
from datetime import timedelta
from .models import Aircraft, Runway

# A list of sample airline code and city codes
airlines = ["BAW", "EZY", "RYR", "AFR", "DLH", "UAE", "AAL", "DAL", "QFA", "SIA"]
cities = ["LHR", "JFK", "CDG", "DXB", "LAX", "AMS", "FRA", "SIN", "HND"]

"""
Function to generate a new random aircraft in the database
is_arrival, false for departure, true for arrival
scheduled_time to set a specified time
emergency_status to set a specified emergency status
"""
def generate_random_aircraft(is_arrival=None, scheduled_time=None, emergency_status='NONE'):
    airline_code = random.choice(airlines)
    flight_number = random.randint(100, 9999)
    callsign = f"{airline_code}{flight_number}"

    # Choose a random origin and destination that are not the same
    origin = random.choice(cities)
    destination = random.choice([c for c in cities if c != origin])

    # If the user didnt specify then choose at random
    if is_arrival is None:
        is_arrival = random.choice([True, False])

    # Arrival: Starts in the holding pattern
    if is_arrival:
        status = 'QUEUE_LA'
        fuel = random.randint(20, 60)

        if scheduled_time:
            s_arrival = scheduled_time
            s_departure = None
        else:
            s_arrival = timezone.now() + timedelta(minutes=random.randint(10, 120))

        # Find an appropriate altitude to start the holding pattern
        holding_pattern_planes = Aircraft.objects.filter(zone_status='QUEUE_LA')
        highest_plane = holding_pattern_planes.order_by('-altitude').first()

        if highest_plane:
            # Set the plane to 1000 ft above the highest plane
            altitude = highest_plane.altitude + 1000
        else:
            # No other planes so we start at 2000 ft
            altitude = 2000

    # Departure logic
    else:
        status = 'QUEUE_TO'
        altitude = 0
        fuel = random.randint(180, 300)  # More fuel for departures

        if scheduled_time:
            s_departure = scheduled_time
            s_arrival = None
        else:
            s_departure = timezone.now() + timedelta(minutes=random.randint(10, 120))

    try:
        Aircraft.objects.create(
            callsign=callsign,
            operator=airline_code,
            origin=origin,
            destination=destination,
            scheduled_arrival=s_arrival,
            scheduled_departure=s_departure,
            altitude=altitude,
            fuel_mins=fuel,
            zone_status=status,
            emergency_status=emergency_status
        )
        print(f"Generated aircraft: {callsign}, Arrival: {is_arrival}, Scheduled Time: {scheduled_time}, Emergency: {emergency_status}")
    except Exception as e:
        print(f"Error generating aircraft: {e}")

"""
Create a random runway in the database
operating_mode defaults to "Mixed"
operational_status defaults to "Available"
"""
def generate_random_runway(operating_mode="Mixed", operational_status="Available"):
    # Generate a random bearing and length
    bearing = random.randint(0, 359)
    length = random.randint(2000, 4000)

    # Derive the runway number from the bearing but make sure it is unique
    bearing_rounded = round(bearing / 10)

    # Try lots of times to create a unique runway number
    for _ in range(36):
        runway_number = f"{bearing_rounded:02d}"

        # Runway doesn't exist yet
        if not Runway.objects.filter(runway_number=runway_number).exists():
            break

        print(f"Runway {runway_number} already exists, trying a new bearing.")
        bearing_rounded = (bearing_rounded + 1) % 36  # Increment and wrap around

    try:
        Runway.objects.create(
            runway_number=runway_number,
            length=length,
            bearing=bearing,
            operating_mode=operating_mode,
            operational_status=operational_status
        )
        print(f"Generated runway: {runway_number}, Bearing: {bearing}, Length: {length}, Mode: {operating_mode}, Status: {operational_status}")
    except Exception as e:
        print(f"Error creating runway: {e}")
    
# Function which processes a tick in the simulation and updates all aircraft in the database
def update_simulation():
    aircrafts = Aircraft.objects.all()
    now = timezone.now()

    # Check that the runways is empty with no aircraft on it
    runway_occupied = aircrafts.filter(zone_status__in=['RUNWAY_LA', 'RUNWAY_TO']).exists()
    # Is the runways available for use?
    active_runway = Runway.objects.filter(operational_status='Available').first()

    for plane in aircrafts:
        # 1 min of fuel is consumed for all planes in the air or queued
        if plane.zone.status in ['QUEUE_LA', 'RUNWAY_LA', 'QUEUE_TO', 'RUNWAY_TO']:
            plane.fuel_mins -= 1
        
        # Fuel emergency check
        if plane.fuel_mins <= 10 and plane.emergency_status == 'NONE':
            plane.emergency_status = 'FUEL'
        
        # Handle emergencies
        if plane.emergency_status != 'NONE':
            # Prioritize landing for emergencies
            if plane.zone_status in ['QUEUE_LA', 'RUNWAY_LA']:
                if not runway_occupied and active_runway:
                    plane.zone_status = 'RUNWAY_LA'
                    runway_occupied = True
            elif plane.zone_status == 'QUEUE_TO':
                # Divert to landing queue
                plane.zone_status = 'QUEUE_LA'