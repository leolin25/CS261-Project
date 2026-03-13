from datetime import timedelta
from .models import Aircraft, Runway


class RunwayController:
    def __init__(self, landing_duration, takeoff_duration, fuel_risk_threshold, takeoff_risk_threshold, max_wait):
        self.landing_duration = landing_duration
        self.takeoff_duration = takeoff_duration
        self.fuel_risk_threshold = fuel_risk_threshold
        self.takeoff_risk_threshold = takeoff_risk_threshold
        self.max_wait = max_wait

    # Assigns a given aircraft to a runway based on its zone status (arriving or departing) and the runway's operating mode. Returns True if a runway is assigned and False is not. Also updates the runway's status to OCCUPIED and saves the assigned runway number in the aircraft's record.
    @staticmethod
    def assign_runway(aircraft, simulation_time):
        available_runways = Runway.objects.filter(operational_status='AVAILABLE', occupied_by__isnull=True)
        if not available_runways.exists():
            return False # No runways available, return False
        
        assigned_runway = None
        if aircraft.zone_status == 'QUEUE_LA': # Arriving flights
            assigned_runway = available_runways.filter(operating_mode__icontains='LANDING').first()
            aircraft.zone_status = 'RUNWAY_LA'
        elif aircraft.zone_status == 'QUEUE_TO': # Departing flights
            assigned_runway = available_runways.filter(operating_mode__icontains='TAKEOFF').first()
            aircraft.zone_status = 'RUNWAY_TO'

        if assigned_runway: # Lock the runway
            assigned_runway.operational_status = 'OCCUPIED'
            # Now saves the plane that occupies it and the time at which it started occupying it.
            assigned_runway.occupied_by = aircraft
            assigned_runway.time_occupied = simulation_time
            assigned_runway.save()
            
            # Tell the plane which runway it got
            aircraft.assigned_runway = assigned_runway
            aircraft.save()
            return True
        return False

    # Takes an aircraft, finds the runway it was holding, and unlocks it. True if successful, False if the plane had no runway assigned or if the runway was not found.
    def free_runway(self, aircraft, simulation_time):
        if not aircraft.assigned_runway:
            return False

        try:
            # Find the runway and unlock it
            runway = Runway.objects.get(id=aircraft.assigned_runway.id)
            if not runway.time_occupied:
                return False

            if aircraft.scheduled_arrival:
                duration = timedelta(seconds=self.landing_duration)
            else:
                duration = timedelta(seconds=self.takeoff_duration)

            if simulation_time - runway.time_occupied < duration:
                return False # Has not been on the runway for long enough

            # Free the runway
            if runway.operational_status == 'OCCUPIED': # Do not change runway status if it is closed
                runway.operational_status = 'AVAILABLE'
            runway.occupied_by = None
            runway.time_occupied = None
            runway.save()
            
            # Erase the runway from the plane's memory
            aircraft.assigned_runway = None
            aircraft.final_state_time = simulation_time
            # Move the plane to the next zone
            if aircraft.zone_status == 'RUNWAY_LA':
                aircraft.zone_status = 'LANDED'
            if aircraft.zone_status == 'RUNWAY_TO':
                aircraft.zone_status = 'DEPARTED'
            aircraft.save()
            
            print(f"Runway {runway.bearing} has been freed.")
            return True
        except Runway.DoesNotExist:
            return False
        
    # This function is called every minute to update the mixed runways based on current traffic, mixed runways are put in a temporary new optimised mode that suits the situation
    def optimise_runway_mode(self, simulation_time):
        risk_time = simulation_time - timedelta(minutes=self.takeoff_risk_threshold) - timedelta(minutes=self.max_wait)

        # In case of any bugs we can reset runways right here
        # self.reset_optimised_runways()

        # Find all mixed runways that are currently available
        mixed_runways = Runway.objects.filter(operational_status='AVAILABLE', operating_mode__icontains='MIXED', occupied_by__isnull=True)
        if not mixed_runways.exists():
            return
        
        # Emergency risks are the most important, calculate them first and that sets the lower bound of landing runways
        emergency_count = Aircraft.objects.filter(zone_status='QUEUE_LA').exclude(emergency_status='NONE').count()
        # Calculate the number of diversion risks for arrivals 
        arrival_risks = Aircraft.objects.filter(zone_status='QUEUE_LA', fuel_mins__lte=self.fuel_risk_threshold).count()
        # Cancellation risks are only relevant for takeoff
        takeoff_risks = Aircraft.objects.filter(zone_status='QUEUE_TO', queue_entry_time__lte=risk_time).count()
        # Calculate the total amount of arriving and departing planes in the queues to use as a tiebreaker if there are no emergency or cancellation risks. We prioritise the one with more traffic to try and reduce the queues overall, as well as prioritising takeoff if there is a tie to try and reduce congestion on the runways, as planes that are about to takeoff have already been waiting on the runway and are more likely to have been delayed by other planes, whereas arriving planes have not yet reached the runway and so are less likely to have been delayed by other planes.
        amount_arriving = Aircraft.objects.filter(zone_status='QUEUE_LA').count()
        amount_departing = Aircraft.objects.filter(zone_status='QUEUE_TO').count()

        for runway in mixed_runways:
            # Emergency risks should always be prioritised over everything else, as they are the most time sensitive and can cause loss of life
            if emergency_count > 0:
                emergency_count -= 1
                amount_arriving -= 1
                runway.operating_mode = 'LANDING'
                runway.temp_optimised = True
            # Prioritise landing if there are more emergency risks, otherwise prioritise takeoff if there are more cancellation risks.
            elif arrival_risks >= takeoff_risks and arrival_risks != 0:
                arrival_risks -= 1
                amount_arriving -= 1
                runway.operating_mode = 'LANDING'
                runway.temp_optimised = True
            elif takeoff_risks > arrival_risks:
                takeoff_risks -= 1
                amount_departing -= 1
                runway.operating_mode = 'TAKEOFF'
                runway.temp_optimised = True
            # No emergency or cancellation risks, so optimise based on which has more traffic
            elif amount_arriving >= amount_departing:
                amount_arriving -= 1
                runway.operating_mode = 'LANDING'
                runway.temp_optimised = True
            elif amount_departing > amount_arriving:
                amount_departing -= 1
                runway.operating_mode = 'TAKEOFF'
                runway.temp_optimised = True
        Runway.objects.bulk_update(mixed_runways, ['operating_mode', 'temp_optimised'])

    # This function resets all runways back to mixed if they have been optimised
    @staticmethod
    def reset_optimised_runways():
        optimised_runways = Runway.objects.filter(temp_optimised=True, occupied_by__isnull=True)
        for runway in optimised_runways:
            runway.operating_mode = 'MIXED'
            runway.temp_optimised = False
        Runway.objects.bulk_update(optimised_runways, ['operating_mode', 'temp_optimised'])