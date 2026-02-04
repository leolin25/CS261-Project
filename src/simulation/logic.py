import random
from django.utils import timezone
from datetime import timedelta
from .models import Aircraft

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

# Function which processes a tick in the simulation and updates all aircraft in the database
def update_simulation():
    aircrafts = Aircraft.objects.all()
    now = timezone.now()

    # Check runway availability