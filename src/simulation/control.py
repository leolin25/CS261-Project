from datetime import timedelta
from django.utils import timezone
from .models import Aircraft, Runway, RunConfig, RunStats
from .generation import Generator
from .RunwayController import RunwayController
from .departure_logic import DepartureController
from .arrival_logic import ArrivalController


class Controller:
    def __init__(self, launch_time=None):
        start_time = launch_time if launch_time else timezone.now()
        self.last_update_time = start_time
        self.simulation_time = start_time
        self.runways = None
        self.mixed_runways = None
        self.takeoff_runways = None
        self.landing_runways = None
        self.inbound_per_hour = None
        self.outbound_per_hour = None
        self.timescale = None #1 second to 1 minute by default
        self.schedule_limit = None
        self.max_wait = None
        self.landing_duration = None
        self.takeoff_duration = None
        self.fuel_risk_threshold = None
        self.takeoff_risk_threshold = None
        self.stop = None
        self.update_configuration(first=True)
        self.generator = Generator(
            self.schedule_limit,
            self.inbound_per_hour,
            self.outbound_per_hour,
            start_time,
        )
        self.runway_controller = RunwayController(
            self.landing_duration,
            self.takeoff_duration,
            self.fuel_risk_threshold,
            self.takeoff_risk_threshold,
        )
        self.departure_controller = DepartureController(
            self.runway_controller,
            self.max_wait,
        )
        self.arrival_controller = ArrivalController(self.runway_controller)

    def update_configuration(self, first=False):
        config = RunConfig.objects.last()
        if not config:
            return False
        self.runways = config.runways
        self.mixed_runways = config.runways_mixed
        self.takeoff_runways = config.runways_takeoff
        self.landing_runways = config.runways_landing
        self.inbound_per_hour = config.inbound_per_hour
        self.outbound_per_hour = config.outbound_per_hour
        self.timescale = config.timescale
        self.schedule_limit = config.schedule_limit
        self.max_wait = config.max_wait
        self.landing_duration = config.landing_duration
        self.takeoff_duration = config.takeoff_duration
        self.fuel_risk_threshold = config.fuel_risk_threshold
        self.takeoff_risk_threshold = config.takeoff_risk_threshold
        self.stop = config.stop
        if not first:
            self.generator.hour_limit = self.schedule_limit
            self.generator.inbound_per_hour = self.inbound_per_hour
            self.generator.outbound_per_hour = self.outbound_per_hour
            self.runway_controller.landing_duration = self.landing_duration
            self.runway_controller.takeoff_duration = self.takeoff_duration
            self.runway_controller.fuel_risk_threshold = self.fuel_risk_threshold
            self.runway_controller.takeoff_risk_threshold = self.takeoff_risk_threshold
            self.departure_controller.max_wait = self.max_wait
        return True

    def check_simulation_end(self):
        return self.stop

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

    @staticmethod
    def get_stream_data():
        flights = Aircraft.objects.all().filter(zone_status__in=["QUEUE_TO", "QUEUE_LA", "RUNWAY_TO", "RUNWAY_LA"])
        #.exclude(zone_status__in=["CANCELLED", "DIVERTED", "LANDED", "DEPARTED"])
        return list(flights)
    

    def run_simulation(self):
        update_start_time = timezone.now()
        self.calculate_new_time((update_start_time - self.last_update_time).total_seconds())
        #print(f"Simulation Time: {self.simulation_time}, Real Time: {update_start_time}")
        self.generator.run_generation(self.simulation_time)
        self.update_aircraft_statuses()
        self.departure_controller.update_aircraft_cancellations(self.simulation_time)
        self.arrival_controller.update_aircraft_fuel(self.simulation_time)
        self.arrival_controller.update_aircraft_diversions()
        self.runway_controller.optimise_runway_mode(self.simulation_time)
        self.departure_controller.process_departures(self.simulation_time)
        self.arrival_controller.process_arrivals(self.simulation_time)
        self.runway_controller.reset_optimised_runways()
        self.last_update_time = update_start_time

        # Log the min/max queue size each tick
        stats = RunStats.objects.first()
        if stats:
            q_la_size = Aircraft.objects.filter(zone_status='QUEUE_LA').count()
            q_to_size = Aircraft.objects.filter(zone_status='QUEUE_TO').count()

            stats.update_max_takeoff_queue(q_to_size)
            stats.update_max_holding_pattern(q_la_size)
            stats.update_min_takeoff_queue(q_to_size)
            stats.update_min_holding_pattern(q_la_size)

    def setup_simulation(self):
        # Clear all existing objects from the database to start fresh   
        Aircraft.objects.all().delete()
        Runway.objects.all().delete()
        RunStats.objects.all().delete()
        for _ in range(self.mixed_runways):
            self.generator.generate_runway(mode="MIXED")
        for _ in range(self.takeoff_runways):
            self.generator.generate_runway(mode="TAKEOFF")
        for _ in range(self.landing_runways):
            self.generator.generate_runway(mode="LANDING")

        # Create a new RunStats object to track statistics for this run
        RunStats.objects.create(id=1)
        
        self.generator.run_generation(self.simulation_time)
