from .models import Aircraft, Runway

class RunwayController:
    def __init__(self):
        self.runways = list(Runway.objects.all())

    # Update the operating mode of the runway (LANDING, TAKEOFF, MIXED)
    def update_mode(self, runway: Runway, mode: str) -> None:
        runway.operating_mode = mode
        runway.save()
        print(f"Runway {runway.runway_number} mode updated to {mode}")

    # Update the status of the runway (AVAILABLE, OCCUPIED, MAINTENANCE)
    def update_status(self, runway: Runway, status: str) -> None:
        runway.operational_status = status
        runway.save()
        print(f"Runway {runway.runway_number} status updated to {status}")

    # Assigns a given aircraft to a runway based on its zone status (arriving or departing) and the runway's operating mode. Returns the assigned runway or None if no suitable runway is available. Also updates the runway's status to OCCUPIED and saves the assigned runway number in the aircraft's record.
    def assign_runway(self, a: Aircraft) -> Runway:
        available_runways = Runway.objects.filter(operational_status='AVAILABLE')

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
            
            print(f"Runway {r.runway_number} has been freed.")
            return True
            
        except Runway.DoesNotExist:
            return False