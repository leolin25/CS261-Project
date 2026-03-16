from .models import Aircraft, RunStats

# Manages all outbound traffic. The key responsibilities include:
# update_aircraft_cancellations() - Marks aircraft 
# which have been in the departure queue longer than the maximum wait time as cancelled

# process_departures() - Frees runways for aircraft which have completed taking 
# off and then assigns available runways to aircrafts in the departure queue in FIFO order

class DepartureController:
    """
    Main logic loop for simulation
    """
    def __init__(self, runway_controller, max_wait):
        self.runway_controller = runway_controller
        self.max_wait = max_wait # Max wait time before flight needs to be cancelled in minutes

    def update_aircraft_cancellations(self, simulation_time):
        aircrafts = Aircraft.objects.filter(zone_status='QUEUE_TO') # Find aircraft in departure queue
        number_cancelled = 0
        for aircraft in aircrafts:
            wait_duration = (simulation_time - aircraft.queue_entry_time).total_seconds() / 60 # Calculate time spent in departure queue so far
            if wait_duration > self.max_wait:
                aircraft.zone_status = 'CANCELLED'
                aircraft.final_state_time = simulation_time
                number_cancelled += 1
                print("Flight {} cancelled".format(aircraft.callsign))
        Aircraft.objects.bulk_update(aircrafts, ['zone_status', 'final_state_time'])

        # Update max cancelled stat if any cancellations occurred
        if number_cancelled > 0:
            stats = RunStats.objects.first()
            if stats:
                total_cancelled = Aircraft.objects.filter(zone_status='CANCELLED').count()
                stats.update_max_cancelled(total_cancelled)

        return number_cancelled

    def process_departures(self, simulation_time):
        departed_aircrafts = Aircraft.objects.filter(zone_status='RUNWAY_TO')
        stats = RunStats.objects.first()

        # Free runways for aircraft that have finished departing
        for aircraft in departed_aircrafts:
            success = self.runway_controller.free_runway(aircraft, simulation_time) # Check if plane has finished departing and free runway if it has
            if success:
                print(f"Flight {aircraft.callsign} has departed.")

                if stats and aircraft.queue_entry_time and aircraft.scheduled_departure:
                    # Update wait time and delay time stats
                    wait_time = (simulation_time - aircraft.queue_entry_time).total_seconds() / 60
                    stats.add_stats(wait_time, 1)
                    delay_time = (simulation_time - aircraft.scheduled_departure).total_seconds() / 60
                    stats.add_stats(delay_time, 3)

                    # Update max and min departure delay
                    stats.update_max_departure_delay(delay_time)
                    stats.update_min_departure_delay(delay_time)

        #Attempt to assign runways to planes in queue, ensuring FIFO ordering
        queue = Aircraft.objects.filter(zone_status='QUEUE_TO').order_by('queue_entry_time')
        for aircraft in queue:
            success = self.runway_controller.assign_runway(aircraft, simulation_time)
            if success:
                aircraft.refresh_from_db()
                print(f"Flight {aircraft.callsign} preparing for takeoff on runway {aircraft.assigned_runway.bearing}")
