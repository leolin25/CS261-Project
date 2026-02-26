from .models import Aircraft, Runway
from django.utils import timezone
from datetime import timedelta

from simulation import models

class RunwayController:
    def __init__(self):
        self.runways = list(Runway.objects.all())

    # Assigns a given aircraft to a runway based on its zone status (arriving or departing) and the runway's operating mode. Returns the assigned runway or None if no suitable runway is available. Also updates the runway's status to OCCUPIED and saves the assigned runway number in the aircraft's record.
    def assign_runway(self, a: Aircraft) -> Runway:
        available_runways = Runway.objects.filter(operational_status='AVAILABLE')

        # No runways available, return None
        if not available_runways.exists():
            return None
        
        assigned_runway = None

        # Arriving flights
        if a.zone_status == 'QUEUE_LA':
            landing = available_runways.filter(operating_mode__icontains='LANDING').first()
            assigned_runway = landing if landing else available_runways.filter(operating_mode__icontains='MIXED').first()
            
        # Departing flights
        elif a.zone_status == 'QUEUE_TO':
            takeoff = available_runways.filter(operating_mode__icontains='TAKEOFF').first()
            assigned_runway = takeoff if takeoff else available_runways.filter(operating_mode__icontains='MIXED').first()

        # Lock the runway
        if assigned_runway:
            assigned_runway.operational_status = 'OCCUPIED'
            assigned_runway.save()
            
            # Tell the plane which runway it got
            a.assigned_runway = assigned_runway.runway_number
            a.save()
            
            return assigned_runway

        return None

    # Takes an aircraft, finds the runway it was holding, and unlocks it. True if successful, False if the plane had no runway assigned or if the runway was not found.
    def free_runway(self, a: Aircraft) -> bool:
        if not a.assigned_runway:
            return False

        try:
            # Find the runway and unlock it
            r = Runway.objects.get(runway_number=a.assigned_runway)
            r.operational_status = 'AVAILABLE'
            r.save()
            
            # Erase the runway from the plane's memory
            a.assigned_runway = None
            a.save()

            # Move the plane to the next zone
            if (a.zone_status == 'RUNWAY_LA'):
                a.zone_status = 'LANDED'
            if (a.zone_status == 'RUNWAY_TO'):
                a.zone_status = 'DEPARTED'
            a.save()
            
            print(f"Runway {r.runway_number} has been freed.")
            return True
            
        except Runway.DoesNotExist:
            return False
        
    # This function is called every minute to update the mixed runways based on current traffic, mixed runways are put in a temporary new optimised mode that suits the sitation
    def optimise_runway_mode(self) -> None:
        now = timezone.now()
        twenty_five_mins_ago = now - timedelta(minutes=25)

        # Find all mixed runways that are currently available
        mixed_runways = Runway.objects.filter(operational_status='AVAILABLE', operating_mode__icontains='MIXED')
        if not mixed_runways.exists():
            return
        
        # Calculate the number of emergency risks and diversion risks for arrivals, and cancellation risks for departures, to determine priority. Emergency risks are planes that have an emergency status or low fuel, diversion risks are planes that have been waiting to land for 25+ mins, and cancellation risks are planes that have been waiting to takeoff for 25+ mins. We also calculate the total amount of arriving and departing planes in the queues to use as a tiebreaker if there are no emergency or cancellation risks.
        emergency_risks = Aircraft.objects.filter(zone_status='QUEUE_LA').filter(models.Q(emergency_status__ne='NONE') | models.Q(fuel_mins__lte=11)).count()
        divert_risks_arrival = Aircraft.objects.filter(zone_status='QUEUE_LA', queue_entry_time__lte=twenty_five_mins_ago).count()
        arrival_priority = emergency_risks + divert_risks_arrival
        
        # Cancellation risks are only relevant for takeoff, as planes that are about to takeoff have already been waiting on the runway and are more likely to have been delayed by other planes, whereas arriving planes have not yet reached the runway and so are less likely to have been delayed by other planes. Therefore we only consider cancellation risks for takeoff when optimising the runways, and not diversion risks for arrival.
        cancel_risks = Aircraft.objects.filter(zone_status='QUEUE_TO', queue_entry_time__lte=twenty_five_mins_ago).count()
        takeoff_priority = cancel_risks

        # Calculate the total amount of arriving and departing planes in the queues to use as a tiebreaker if there are no emergency or cancellation risks. We prioritise the one with more traffic to try and reduce the queues overall, as well as prioritising takeoff if there is a tie to try and reduce congestion on the runways, as planes that are about to takeoff have already been waiting on the runway and are more likely to have been delayed by other planes, whereas arriving planes have not yet reached the runway and so are less likely to have been delayed by other planes.
        amount_arriving = Aircraft.objects.filter(zone_status='QUEUE_LA').count()
        amount_departing = Aircraft.objects.filter(zone_status='QUEUE_TO').count()

        for runway in mixed_runways:
            # Prioritise landing if there are more emergency risks, otherwise prioritise takeoff if there are more cancellation risks.
            if arrival_priority > takeoff_priority:
                arrival_priority = arrival_priority - 1
                runway.operating_mode = 'LANDING'
                runway.temp_optimised = True
                runway.save()
            elif takeoff_priority > arrival_priority:
                takeoff_priority = takeoff_priority - 1
                runway.operating_mode = 'TAKEOFF'
                runway.temp_optimised = True
                runway.save()
            
            # No emergency or cancellation risks, so optimise based on which has more traffic
            elif amount_arriving > amount_departing:
                amount_arriving = amount_arriving - 1
                runway.operating_mode = 'LANDING'
                runway.temp_optimised = True
                runway.save()
            elif amount_departing > amount_arriving:
                amount_departing = amount_departing - 1
                runway.operating_mode = 'TAKEOFF'
                runway.temp_optimised = True
                runway.save()

            # Default to landing if there is a tie, as landing is generally more time sensitive
            else:
                runway.operating_mode = 'LANDING'
                runway.temp_optimised = True
                runway.save()

    # This function resets all runways back to mixed if they have been optimised
    def reset_optimised_runways(self) -> None:
        optimised_runways = Runway.objects.filter(temp_optimised=True)
        for runway in optimised_runways:
            runway.operating_mode = 'MIXED'
            runway.temp_optimised = False
            runway.save()