from datetime import timedelta
from django.utils import timezone
from .models import Aircraft, Runway, RunConfig, RunStats
from .generation import Generator
from .RunwayController import RunwayController
from .departure_logic import DepartureController
from .arrival_logic import ArrivalController


class Controller:
    def __init__(self, launch_time=None):
        start_time = launch_time if launch_time else timezone.now() # Simulation start time
        self.last_update_time = start_time # Real time of last tick
        self.simulation_time = start_time # Simulation time of last tick
        self.runways = None # Number of runways totally
        self.mixed_runways = None # Number of mixed runways
        self.takeoff_runways = None # Number of takeoff runways
        self.landing_runways = None # Number of landing runways
        self.inbound_per_hour = None # Number of inbound flights per hour
        self.outbound_per_hour = None # Number of outbound flights per hour
        self.timescale = None # Simulation timescale (1 timescale equals 1 real second as 1 simulation minute)
        self.schedule_limit = None # How many hours to generate aircraft for
        self.max_wait = None # Maximum wait time in departure queue before cancellation in minutes
        self.landing_duration = None # Time taken for aircraft to land and move off runway in seconds
        self.takeoff_duration = None # Time taken for aircraft to move onto runway and takeoff in seconds
        self.fuel_risk_threshold = None # Amount of fuel left after which aircraft considered diversion risk in minutes
        self.takeoff_risk_threshold = None # Amount of time left before forced cancellation at which aircraft considered cancellation risk in minutes
        self.fuel_emergency_threshold = None # Amount of fuel left after which aircraft declared fuel emergency in minutes
        self.random_events = None # Generate random events or not
        self.stop = None # Flag to stop simulation
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
            self.max_wait,
        )
        self.departure_controller = DepartureController(
            self.runway_controller,
            self.max_wait,
        )
        self.arrival_controller = ArrivalController(
            self.runway_controller,
            self.fuel_emergency_threshold,
        )

    # Reload all config variables from database and pass new values to controllers
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
        self.fuel_emergency_threshold = config.fuel_emergency_threshold
        self.random_events = config.random_events
        self.stop = config.stop
        if not first:
            self.generator.hour_limit = self.schedule_limit
            self.generator.inbound_per_hour = self.inbound_per_hour
            self.generator.outbound_per_hour = self.outbound_per_hour
            self.runway_controller.landing_duration = self.landing_duration
            self.runway_controller.takeoff_duration = self.takeoff_duration
            self.runway_controller.fuel_risk_threshold = self.fuel_risk_threshold
            self.runway_controller.takeoff_risk_threshold = self.takeoff_risk_threshold
            self.runway_controller.max_wait = self.max_wait
            self.departure_controller.max_wait = self.max_wait
            self.arrival_controller.fuel_emergency_threshold = self.fuel_emergency_threshold
        return True

    # Check if simulation has ended
    def check_simulation_end(self):
        return self.stop

    # Get current simulation time
    def get_simulation_time(self):
        return self.simulation_time

    # Find new simulation time based on simulation timescale and real time elapsed
    def calculate_new_time(self, time_elapsed):
        self.simulation_time += timedelta(minutes=(time_elapsed * self.timescale))

    # Move aircraft to respective queue based on expected time
    def update_aircraft_statuses(self):
        aircrafts = Aircraft.objects.filter(zone_status="SCHEDULED", queue_entry_time__lte=self.simulation_time)
        new_arrival = False
        for aircraft in aircrafts:
            if aircraft.scheduled_arrival:
                aircraft.zone_status = "QUEUE_LA"
                new_arrival = True
            elif aircraft.scheduled_departure :
                aircraft.zone_status = "QUEUE_TO"
        Aircraft.objects.bulk_update(aircrafts, ['zone_status'])

        # If a plane gets added to the arrival queue then update altitudes immediately 
        if new_arrival:
            self.arrival_controller.recalculate_altitudes()


    # Collect and return aircraft data for stream(SSE)
    @staticmethod
    def get_stream_data(limit=5):
        flights = Aircraft.objects.all().filter(zone_status__in=["QUEUE_TO", "QUEUE_LA", "RUNWAY_TO", "RUNWAY_LA"]).order_by('queue_entry_time')
        arrivals_schedule = Aircraft.objects.filter(scheduled_arrival__isnull=False, zone_status="SCHEDULED").order_by('scheduled_arrival')[:limit]
        departures_schedule = Aircraft.objects.filter(scheduled_departure__isnull=False, zone_status="SCHEDULED").order_by('scheduled_departure')[:limit]
        arrivals = Aircraft.objects.filter(zone_status="LANDED").order_by('-final_state_time')[:limit]
        departures = Aircraft.objects.filter(zone_status="DEPARTED").order_by('-final_state_time')[:limit]
        cancelled = Aircraft.objects.filter(zone_status="CANCELLED").order_by('-final_state_time')[:limit]
        diverted = Aircraft.objects.filter(zone_status="DIVERTED").order_by('-final_state_time')[:limit]
        return list(flights) + list(arrivals_schedule) + list(departures_schedule) + list(arrivals) + list(departures) + list(cancelled) + list(diverted)
    

    # Main function to run a single tick of simulation
    def run_simulation(self):
        update_start_time = timezone.now() # Real time at tick start
        self.calculate_new_time((update_start_time - self.last_update_time).total_seconds()) # Calculate new simulation time
        #print(f"Simulation Time: {self.simulation_time}, Real Time: {update_start_time}")
        self.generator.run_generation(self.simulation_time, random_events=self.random_events) # Generate new aircraft if needed
        self.update_aircraft_statuses() # Move aircraft to respective queues as needed
        self.departure_controller.update_aircraft_cancellations(self.simulation_time) # Cancel flights that have waited too lond
        self.arrival_controller.update_aircraft_fuel(self.simulation_time) # Decrement fuel of flights waiting in holding pattern
        self.arrival_controller.update_aircraft_diversions(self.simulation_time) # Divert flights that have run out of fuel
        self.runway_controller.optimise_runway_mode(self.simulation_time) # Convert mixed runways to single use based on queue situation and emergencies
        self.departure_controller.process_departures(self.simulation_time) # Process departing aircraft
        self.arrival_controller.process_arrivals(self.simulation_time) # Process arriving aircraft
        self.runway_controller.reset_optimised_runways() # Reset optimised mixed runways
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
        # Generate runways
        for _ in range(self.mixed_runways):
            self.generator.generate_runway(mode="MIXED")
        for _ in range(self.takeoff_runways):
            self.generator.generate_runway(mode="TAKEOFF")
        for _ in range(self.landing_runways):
            self.generator.generate_runway(mode="LANDING")

        # Create a new RunStats object to track statistics for this run
        RunStats.objects.create(id=1)

        # Generate aircraft
        self.generator.run_generation(self.simulation_time, random_events=self.random_events)
