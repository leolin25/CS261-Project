from .models import Aircraft
from numpy import random
from datetime import timedelta, datetime

class Generator:
    def __init__(self, hour_limit, inbound_per_hour, outbound_per_hour):
        self.inbound_schedule = []
        self.outbound_schedule = []
        self.hour_limit = hour_limit
        self.inbound = inbound_per_hour
        self.outbound = outbound_per_hour
        self.last_generated_inbound = datetime.now()
        self.last_generated_outbound = datetime.now()

    @staticmethod
    def generate_delay():
        # Average delay of 0 minutes with a standard deviation of 5 minutes
        return int(round(random.normal(loc=0, scale=5)))

    @staticmethod
    def generate_fuel():
        # Random fuel between 20 and 60 minutes for arrivals, 180 to 300 for departures
        return random.randint(20, 60)

    def generate_aircraft(self, is_arrival):
        delay = self.generate_delay()
        if is_arrival:
            scheduled_time = self.last_generated_inbound + timedelta(minutes=round(60/self.inbound))
        else:
            scheduled_time = self.last_generated_outbound + timedelta(minutes=round(60/self.outbound))
        expected_time = scheduled_time + timedelta(minutes=delay)
        fuel = self.generate_fuel()
        aircraft = Aircraft(
            callsign="123",
            operator="TEST",
            origin="AAA",
            destination="BBB",
            scheduled_arrival=scheduled_time,
            scheduled_departure=scheduled_time,
            queue_entry_time=expected_time,
            altitude=1000,
            fuel_mins=fuel,
            emergency_status='NONE',
            zone_status='SCHEDULED'
        )
        if is_arrival:
            self.last_generated_inbound = scheduled_time
            self.inbound_schedule.append(aircraft)
        else:
            self.last_generated_outbound = scheduled_time
            self.outbound_schedule.append(aircraft)
        return aircraft

    def run_generation(self):
        while datetime.now() + timedelta(hours=self.hour_limit) > self.last_generated_inbound:
            self.generate_aircraft(is_arrival=True)

        while datetime.now() + timedelta(hours=self.hour_limit) > self.last_generated_outbound:
            self.generate_aircraft(is_arrival=False)

        self.inbound_schedule = sorted(self.inbound_schedule, key=lambda aircraft: aircraft.queue_entry_time)
        self.outbound_schedule = sorted(self.outbound_schedule, key=lambda aircraft: aircraft.queue_entry_time)
        return self.inbound_schedule, self.outbound_schedule
