from datetime import timedelta
from django.utils import timezone
from .models import Aircraft, Runway
from .generation import Generator
from .RunwayController import RunwayController


class Controller:
    def __init__(self, runways, inbound_per_hour, outbound_per_hour, launch_time=None, timescale=1, schedule_limit=12, max_wait=30):
        start_time = launch_time if launch_time else timezone.now()
        self.runways = runways
        self.inbound_per_hour = inbound_per_hour
        self.outbound_per_hour = outbound_per_hour
        self.last_update_time = start_time
        self.simulation_time = start_time
        self.timescale = timescale #1 second to 1 minute by default
        self.schedule_limit = schedule_limit
        self.max_wait = max_wait
        self.generator = Generator(self.schedule_limit, self.inbound_per_hour, self.outbound_per_hour, start_time)
        self.runway_controller = RunwayController()

    def calculate_new_time(self, time_elapsed):
        self.simulation_time += timedelta(minutes=(time_elapsed * self.timescale))

    def update_aircraft_statuses(self):
        aircrafts = Aircraft.objects.filter(zone_status="SCHEDULED", queue_entry_time__lte=self.simulation_time)
        for aircraft in aircrafts:
            if aircraft.scheduled_arrival:
                aircraft.zone_status = "QUEUE_LA"
            elif aircraft.scheduled_departure :
                aircraft.zone_status = "QUEUE_TO"
        Aircraft.objects.bulk_update(aircrafts, ['zone_status'])

    def update_aircraft_cancellations(self):
        aircrafts = Aircraft.objects.filter(zone_status='QUEUE_TO')
        number_cancelled = 0
        for aircraft in aircrafts:
            wait_duration = (self.simulation_time - aircraft.queue_entry_time).total_seconds() / 60
            if wait_duration > self.max_wait:
                aircraft.zone_status = 'CANCELLED'
                number_cancelled += 1
                print("Flight {} cancelled".format(aircraft.callsign))
        Aircraft.objects.bulk_update(aircrafts, ['zone_status'])
        return number_cancelled

    @staticmethod
    def get_stream_data():
        inbound_schedule = Aircraft.objects.filter(zone_status="SCHEDULED", scheduled_departure=None).order_by('queue_entry_time')
        outbound_schedule = Aircraft.objects.filter(zone_status="SCHEDULED", scheduled_arrival=None).order_by('queue_entry_time')
        return list(inbound_schedule) + list(outbound_schedule)

    def run_simulation(self):
        update_start_time = timezone.now()
        self.calculate_new_time((update_start_time - self.last_update_time).total_seconds())
        #print(f"Simulation Time: {self.simulation_time}, Real Time: {update_start_time}")
        self.generator.run_generation(self.simulation_time)
        self.update_aircraft_statuses()
        self.update_aircraft_cancellations()
        self.runway_controller.optimise_runway_mode(self.simulation_time)
        self.runway_controller.reset_optimised_runways()
        self.last_update_time = update_start_time

    def setup_simulation(self):
        Aircraft.objects.all().delete()
        Runway.objects.all().delete()
        for _ in range(self.runways):
            self.generator.generate_runway()
        self.generator.run_generation(self.simulation_time)
