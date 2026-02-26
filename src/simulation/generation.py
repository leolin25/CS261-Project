from datetime import timedelta
from django.conf import settings
from numpy import random
import pandas as pd
from .models import Aircraft
from django.utils import timezone


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
    def generate_fuel():
        # Random fuel between 20 and 60 minutes for arrivals
        return random.randint(20, 60)

    def generate_aircraft(self, is_arrival):
        delay = self.generate_delay()
        if is_arrival:
            scheduled_time = self.last_generated_inbound + timedelta(minutes=round(60 / self.inbound_per_hour))
        else:
            scheduled_time = self.last_generated_outbound + timedelta(minutes=round(60 / self.outbound_per_hour))
        expected_time = scheduled_time + timedelta(minutes=delay)
        fuel = self.generate_fuel()
        data = self.data.sample()
        aircraft = Aircraft(
            callsign=data["carrier"].values[0] + str(data["flight"].values[0]),
            operator=data["name"].values[0],
            origin=data["origin"].values[0],
            destination=data["dest"].values[0],
            scheduled_arrival=scheduled_time if is_arrival else None,
            scheduled_departure=scheduled_time if not is_arrival else None,
            queue_entry_time=expected_time,
            altitude=1000 if is_arrival else 0, #Default altitude for new aircraft
            fuel_mins=fuel,
            emergency_status='NONE',
            zone_status='SCHEDULED',
            last_update=expected_time #Only need to consider plane when it enters airport zone
        )
        if is_arrival:
            self.last_generated_inbound = scheduled_time
        else:
            self.last_generated_outbound = scheduled_time
        return aircraft

    def run_generation(self):
        while (timezone.now() + timedelta(hours=self.hour_limit) > self.last_generated_inbound and
               self.inbound_per_hour > 0):
            self.generate_aircraft(is_arrival=True).save()

        while (timezone.now()+ timedelta(hours=self.hour_limit) > self.last_generated_outbound and
               self.outbound_per_hour > 0):
            self.generate_aircraft(is_arrival=False).save()

        inbound_schedule = Aircraft.objects.filter(zone_status="SCHEDULED", scheduled_departure=None).order_by('queue_entry_time')
        outbound_schedule = Aircraft.objects.filter(zone_status="SCHEDULED", scheduled_arrival=None).order_by('queue_entry_time')
        return inbound_schedule, outbound_schedule
