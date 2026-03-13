from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from numpy import random
from random import randint
import pandas as pd
from .models import Aircraft, Runway


class Generator:
    def __init__(self, hour_limit, inbound_per_hour, outbound_per_hour, start_time=None):
        self.hour_limit = hour_limit
        self.inbound_per_hour = inbound_per_hour
        self.outbound_per_hour = outbound_per_hour
        base_time = start_time if start_time is not None else timezone.now()
        self.last_generated_inbound = base_time
        self.last_generated_outbound = base_time
        self.data = pd.read_csv(settings.BASE_DIR / 'simulation' / 'data' / 'flight-data.csv')

    @staticmethod
    def generate_delay():
        # Average delay of 0 minutes with a standard deviation of 5 minutes
        return int(round(random.normal(loc=0, scale=5)))

    @staticmethod
    def generate_fuel(is_arrival):
        # Random fuel between 20 and 60 minutes for arrivals
        return random.randint(20, 60) if is_arrival else random.randint(180, 360)

    @staticmethod
    # This function will generate a random event with p=0.01 otherwise it will return 'NONE' indicating no event
    def generate_random_event():
        # Generate a random number between 0 and 1
        if random.random() < 0.01:
            # Return a random event (e.g., 'MEDICAL', 'MECHANICAL')
            return random.choice(['MEDICAL', 'MECHANICAL'])
        else:
            return 'NONE'

    def generate_aircraft(self, is_arrival):
        delay = self.generate_delay()
        if is_arrival:
            scheduled_time = self.last_generated_inbound + timedelta(minutes=60 / self.inbound_per_hour)
        else:
            scheduled_time = self.last_generated_outbound + timedelta(minutes=60 / self.outbound_per_hour)
        expected_time = scheduled_time + timedelta(minutes=delay)
        fuel = self.generate_fuel(is_arrival)
        data = self.data.sample()
        random_event = self.generate_random_event()
        aircraft = Aircraft(
            callsign=data["carrier"].values[0] + str(data["flight"].values[0]),
            operator=data["name"].values[0],
            origin=data["origin"].values[0],
            destination=data["dest"].values[0],
            scheduled_arrival=scheduled_time if is_arrival else None,
            scheduled_departure=scheduled_time if not is_arrival else None,
            queue_entry_time=expected_time,
            assigned_runway=None,
            altitude=1000 if is_arrival else 0, #Default altitude for new aircraft
            fuel_mins=fuel,
            emergency_status=random_event,
            zone_status='SCHEDULED',
            last_update=expected_time, #Only need to consider plane when it enters airport zone
            final_state_time=None
        )
        if is_arrival:
            self.last_generated_inbound = scheduled_time
        else:
            self.last_generated_outbound = scheduled_time
        return aircraft

    @staticmethod
    def generate_runway(mode="MIXED", status="AVAILABLE"):
        bearing = randint(0, 35)
        length = randint(2000, 4000)
        Runway.objects.create(
            bearing=bearing,
            length=length,
            operating_mode=mode,
            operational_status=status,
        )
        print("Runway created with bearing {} and length {}".format(bearing, length))

    def run_generation(self, simulation_time=timezone.now()):
        while (simulation_time + timedelta(hours=self.hour_limit) > self.last_generated_inbound and
               self.inbound_per_hour > 0):
            self.generate_aircraft(is_arrival=True).save()

        while (simulation_time + timedelta(hours=self.hour_limit) > self.last_generated_outbound and
               self.outbound_per_hour > 0):
            self.generate_aircraft(is_arrival=False).save()
