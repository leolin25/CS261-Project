import random
from django.utils import timezone
from datetime import timedelta
from .models import Aircraft, Runway, FlightStats

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

    callsign = ""

    for _ in range(50):  # Try up to 50 times to find a unique callsign
        callsign = f"{airline_code}{flight_number}"
        if not Aircraft.objects.filter(callsign=callsign).exists():
            break
        flight_number = random.randint(100, 9999)  # Generate a new flight number if not unique

    # Choose a random origin and destination that are not the same
    origin = random.choice(cities)
    destination = random.choice([c for c in cities if c != origin])

    # If the user didnt specify then choose at random
    if is_arrival is None:
        is_arrival = random.choice([True, False])

    status = 'SCHEDULED'  # Default status for new aircraft
    altitude = 0

    # Variance in time
    error_mins = random.gauss(0, 5)
    q_time = scheduled_time + timedelta(minutes=error_mins) if scheduled_time else None

    # Arrival: Starts in the holding pattern
    if is_arrival:
        fuel = random.randint(20, 60)
        s_arrival = scheduled_time
        s_departure = None

    # Departure logic
    else:
        fuel = random.randint(180, 300)  # More fuel for departures
        s_arrival = None
        s_departure = scheduled_time

    try:
        Aircraft.objects.create(
            callsign=callsign,
            operator=airline_code,
            origin=origin,
            destination=destination,
            scheduled_arrival=s_arrival,
            scheduled_departure=s_departure,
            queue_entry_time=q_time,
            altitude=altitude,
            fuel_mins=fuel,
            zone_status=status,
            emergency_status=emergency_status
        )
        print(f"Generated aircraft: {callsign}, Arrival: {is_arrival}, Scheduled Time: {scheduled_time}, Emergency: {emergency_status}")
    except Exception as e:
        print(f"Error generating aircraft: {e}")

# Function to create a new flight statistics entry in the database
def create_flight_stats(plane, current_time):
    # Initialize defaults
    hold_time = 0.0
    takeoff_time = 0.0
    arr_delay = 0.0
    dep_delay = 0.0

    # Arrival stats
    if plane.scheduled_arrival:
        # Holding time = now - queue_entry_time
        duration = (current_time - plane.queue_entry_time).total_seconds() / 60.0
        hold_time = max(0.0, duration)

        # Arrival delay = now - scheduled_arrival (can be negative)
        arr_delay = (current_time - plane.scheduled_arrival).total_seconds() / 60.0

    # Departure stats
    if plane.scheduled_departure:
        # Takeoff queue time = now - queue_entry_time
        duration = (current_time - plane.queue_entry_time).total_seconds() / 60.0
        takeoff_time = max(0.0, duration)

        # Departure delay = now - scheduled_departure (can be negative)
        dep_delay = (current_time - plane.scheduled_departure).total_seconds() / 60.0

    try:
        FlightStats.objects.create(
            callsign=plane.callsign,
            holding_time_mins=hold_time,
            takeoff_queue_time_mins=takeoff_time,
            arrival_delay_mins=arr_delay,
            departure_delay_mins=dep_delay,
            outcome=plane.zone_status
        )
        print(f"Created stats for {plane.callsign}: Hold {hold_time} mins, Takeoff Queue {takeoff_time} mins, Arrival Delay {arr_delay} mins, Departure Delay {dep_delay} mins")
    except Exception as e:
        print(f"Error creating flight stats for {plane.callsign}: {e}")

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
    # Scheduled flights should now be simulated
    hidden_planes = aircrafts.filter(zone_status='SCHEDULED')

    for plane in hidden_planes:
        if plane.queue_entry_time and now >= plane.queue_entry_time:
            # Check if it's time for arrivals
            if plane.scheduled_arrival:
                plane.zone_status = 'QUEUE_LA'
                holding_planes = Aircraft.objects.filter(zone_status='QUEUE_LA')
                highest = holding_planes.order_by('-altitude').first()
                plane.altitude = (highest.altitude + 1000) if highest else 2000
                print(f"ACTIVATED Arrival {plane.callsign}")
        
            # Check if it's time for departures
            elif plane.scheduled_departure and now >= plane.scheduled_departure:
                plane.zone_status = 'QUEUE_TO'
                plane.altitude = 0
                print(f"ACTIVATED Departure {plane.callsign}")

            plane.save()
        