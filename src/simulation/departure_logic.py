from .models import Aircraft, RunStats

class DepartureController:
    """
    Main logic loop for simulation
    """
    def __init__(self, runway_controller):
        self.runway_controller = runway_controller

    def process_departures(self, simulation_time):
        departed_aircrafts = Aircraft.objects.filter(zone_status='RUNWAY_TO')
        for aircraft in departed_aircrafts:
            success = self.runway_controller.free_runway(aircraft, simulation_time)
            if success:
                print(f"Flight {aircraft.callsign} has departed.")
                aircraft.zone_status = 'DEPARTED'
                aircraft.save()

                # Stat log for the departed flight
                wait_time = (simulation_time - aircraft.queue_entry_time).total_seconds() / 60
                delay_time = (simulation_time - aircraft.scheduled_departure).total_seconds() / 60
                stats = RunStats.objects.first()

                stats.add_stats(wait_time, 1)
                stats.add_stats(delay_time, 3)
                stats.update_max_departure_delay(delay_time)
                stats.update_min_departure_delay(delay_time)

        #Attempt to assign runways to planes in queue, ensuring FIFO ordering
        queue = Aircraft.objects.filter(zone_status='QUEUE_TO').order_by('queue_entry_time')
        for aircraft in queue:
            success = self.runway_controller.assign_runway(aircraft, simulation_time)
            if success:
                aircraft.refresh_from_db()
                print(f"Flight {aircraft.callsign} preparing for takeoff on runway {aircraft.assigned_runway.bearing}")
