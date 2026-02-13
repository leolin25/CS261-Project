from .models import Aircraft, Runway

class RunwayController:
    def __init__(self):
        # We fetch all runways from the DB to initialize the list
        self.runways = list(Runway.objects.all())

    def update_mode(self, runway: Runway, mode: str) -> None:
        # Updates the operating mode (e.g., 'Takeoff Only', 'Mixed')
        runway.operating_mode = mode
        runway.save()
        print(f"{runway.runway_number} mode updated to {mode}")

    def update_status(self, runway: Runway, status: str) -> None:
        # Updates operational status (e.g., 'Available', 'Closed')
        runway.operational_status = status
        runway.save()
        print(f"{runway.runway_number} status updated to {status}")

    def assign_runway(self, a: Aircraft):
        """
        Finds a runway that is appropriate for the Aircraft. Returns True if found and False if not found.
        
        :param self: The runway controller
        :param a: The passed aircraft
        :type a: Aircraft
        """
        # Get dynamically available runways (in case statuses changed)
        available_runways = Runway.objects.filter(operational_status='AVAILABLE')

        # No available runways
        if not available_runways:
            return False
        
        assign_runway = False

        # Arriving flights
        if a.zone_status == 'QUEUE_LA':
            # Try Landing Only first
            landing = available_runways.filter(operating_mode__icontains='LANDING').first()
            if landing:
                assigned_runway = landing
            else:
                # Fallback to Mixed
                assigned_runway = available_runways.filter(operating_mode__icontains='MIXED').first()
        # Departing flights
        elif a.zone_status == 'QUEUE_TO':
            # Try Takeoff Only first
            takeoff = available_runways.filter(operating_mode__icontains='TAKEOFF').first()
            if takeoff:
                assigned_runway = takeoff
            else:
                # Fallback to Mixed
                assigned_runway = available_runways.filter(operating_mode__icontains='MIXED').first()

        # Lock the runway as occupied and set the airplane's assigned runway
        if assigned_runway:
            assigned_runway.operational_status = 'OCCUPIED'
            assigned_runway.save()
            
            # Tell the plane which runway it got
            a.assigned_runway = assigned_runway.runway_number
            a.zone_status = "RUNWAY_LA" if a.zone_status=="QUEUE_LA" else "RUNWAY_TO"
            a.altitude = 0
            a.save()
            
            return True

        return False

    def schedule_movement(self) -> None:
        """
        First, it clears finished planes off the runways.
        Second, it assigns queued planes to the newly opened runways.
        """
        
        active_runway_planes = Aircraft.objects.filter(zone_status__in=['RUNWAY_LA', 'RUNWAY_TO'])
        
        for plane in active_runway_planes:
            # Unlock the runway
            if plane.assigned_runway:
                try:
                    r = Runway.objects.get(runway_number=plane.assigned_runway)
                    r.operational_status = 'AVAILABLE'
                    r.save()
                except Runway.DoesNotExist:
                    pass
            
            # Advance the plane's state
            if plane.zone_status == 'RUNWAY_LA':
                plane.zone_status = 'LANDED'
            elif plane.zone_status == 'RUNWAY_TO':
                plane.zone_status = 'DEPARTED'
                plane.altitude = 5000
                
            plane.save()

        waiting_planes = Aircraft.objects.filter(zone_status__in=['QUEUE_LA', 'QUEUE_TO'])
        
        for plane in waiting_planes:
            # Emergency/Altitude priority for landings
            is_priority = (plane.emergency_status != 'NONE') or (plane.altitude <= 2000)
            if plane.zone_status == 'QUEUE_LA' and not is_priority:
                continue 

            # Ask the helper for a runway ticket
            found_runway = self.assign_runway(plane)

            if found_runway:
                # Physically move the plane onto the runway
                if plane.zone_status == 'RUNWAY_LA':
                    # Drop the holding stack
                    stack = Aircraft.objects.filter(zone_status='QUEUE_LA').exclude(id=plane.id)
                    for p in stack:
                        if p.altitude > 2000:
                            p.altitude -= 1000
                            p.save()

                plane.save()