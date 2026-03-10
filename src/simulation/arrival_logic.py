from datetime import timedelta
from .models import Aircraft, RunStats


"""
This class manages the arrival of planes, including the holding pattern and diverting planes that have been waiting for too long or have low fuel.
"""
class ArrivalController:
    def __init__(self, runway_controller):
        self.runway_controller = runway_controller

    """
    Decrease the fuel level of all planes in the holding pattern by 1 min, this function should be called by main every minute tick
    """
    @staticmethod
    def update_aircraft_fuel(simulation_time):
        aircrafts = Aircraft.objects.filter(zone_status='QUEUE_LA', last_update__lte=simulation_time-timedelta(minutes=1))
        for aircraft in aircrafts:
            aircraft.fuel_mins = max(0, aircraft.fuel_mins - 1)
            aircraft.last_update += timedelta(minutes=1)
        Aircraft.objects.bulk_update(aircrafts, ['fuel_mins', 'last_update'])

    @staticmethod
    def update_aircraft_diversions():
        aircrafts = Aircraft.objects.filter(zone_status='QUEUE_LA', fuel_mins__lte=10)
        num_diverted = 0
        for aircraft in aircrafts:
            aircraft.zone_status = 'DIVERTED'
            num_diverted += 1
            print(f"Flight {aircraft.callsign} diverted due to low fuel")
        Aircraft.objects.bulk_update(aircrafts, ['zone_status'])

        if num_diverted > 0:
            stats = RunStats.objects.first()
            if stats:
                total_diverted = Aircraft.objects.filter(zone_status='DIVERTED').count()
                stats.update_max_diverted(total_diverted)

    def process_arrivals(self, simulation_time):
        stats = RunStats.objects.first()
        arrived_aircrafts = Aircraft.objects.filter(zone_status='RUNWAY_LA')
        for aircraft in arrived_aircrafts:
            success = self.runway_controller.free_runway(aircraft, simulation_time)
            if success:
                print(f"Flight {aircraft.callsign} has landed.")

                if stats and aircraft.queue_entry_time and aircraft.scheduled_arrival:
                    # Update wait time and delay time stats
                    wait_time = (simulation_time - aircraft.queue_entry_time).total_seconds() / 60
                    stats.add_stats(wait_time, 0)
                    delay_time = (simulation_time - aircraft.scheduled_arrival).total_seconds() / 60
                    stats.add_stats(delay_time, 2)

                    # Update max and min arrival delay
                    stats.update_max_arrival_delay(delay_time)
                    stats.update_min_arrival_delay(delay_time)

        emergencies = Aircraft.objects.filter(zone_status='QUEUE_LA', emergency_status__in=['MEDICAL', 'MECHANICAL', 'FUEL']).order_by('queue_entry_time')
        general = Aircraft.objects.filter(zone_status='QUEUE_LA', emergency_status='NONE').order_by('queue_entry_time')
        queue = list(emergencies) + list(general)
        for aircraft in queue:
            success = self.runway_controller.assign_runway(aircraft, simulation_time)
            if success:
                aircraft.refresh_from_db()
                print(f"Flight {aircraft.callsign} preparing for landing on runway {aircraft.assigned_runway.bearing}")
