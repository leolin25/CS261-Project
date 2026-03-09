from .models import Aircraft


class DepartureController:
    """
    Main logic loop for simulation
    """
    def __init__(self, runway_controller, max_wait):
        self.runway_controller = runway_controller
        self.max_wait = max_wait

    def update_aircraft_cancellations(self, simulation_time):
        aircrafts = Aircraft.objects.filter(zone_status='QUEUE_TO')
        number_cancelled = 0
        for aircraft in aircrafts:
            wait_duration = (simulation_time - aircraft.queue_entry_time).total_seconds() / 60
            if wait_duration > self.max_wait:
                aircraft.zone_status = 'CANCELLED'
                number_cancelled += 1
                print("Flight {} cancelled".format(aircraft.callsign))
        Aircraft.objects.bulk_update(aircrafts, ['zone_status'])
        return number_cancelled

    def process_departures(self, simulation_time):
        departed_aircrafts = Aircraft.objects.filter(zone_status='RUNWAY_TO')
        for aircraft in departed_aircrafts:
            success = self.runway_controller.free_runway(aircraft, simulation_time)
            if success:
                print(f"Flight {aircraft.callsign} has departed.")

        #Attempt to assign runways to planes in queue, ensuring FIFO ordering
        queue = Aircraft.objects.filter(zone_status='QUEUE_TO').order_by('queue_entry_time')
        for aircraft in queue:
            success = self.runway_controller.assign_runway(aircraft, simulation_time)
            if success:
                aircraft.refresh_from_db()
                print(f"Flight {aircraft.callsign} preparing for takeoff on runway {aircraft.assigned_runway.bearing}")
