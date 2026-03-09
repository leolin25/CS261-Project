from datetime import timedelta
from .models import Aircraft, RunStats

class ArrivalManager:
    # Minimum fuel level before diverting
    min_fuel_level = 11 
    
    @staticmethod
    def check_divertion(time):
        """
        Divert flights that have waited longer than 30 minutes in the 
        holding pattern, or have fuel <= 11min
        """
        in_queue = Aircraft.objects.filter(zone_status='QUEUE_LA')
        num_diverted_planes = 0 
        stats = RunStats.objects.first() # Grab the stats tracker

        for plane in in_queue:
            wait_duration = (time - plane.queue_entry_time).total_seconds() / 60

            # Divert if wait is > 30mins OR fuel is critically low
            if wait_duration > 30 or plane.fuel_mins <= ArrivalManager.min_fuel_level:
                plane.zone_status = 'DIVERTED'
                plane.save()
                num_diverted_planes += 1
                
                reason = "waiting time" if wait_duration > 30 else "low fuel"
                print(f"Flight {plane.callsign} diverted due to {reason}")

        # Log the max diverted planes if any were diverted this minute
        if num_diverted_planes > 0 and stats:
            stats.update_max_diverted(num_diverted_planes)

        return num_diverted_planes
        
    @staticmethod
    def decrease_fuel():
        """
        Decrease the fuel level of all planes in the holding pattern by 1 min.
        """
        in_queue = Aircraft.objects.filter(zone_status='QUEUE_LA')
        for plane in in_queue:
            plane.fuel_mins = max(0, plane.fuel_mins - 1)
            plane.save()

    @staticmethod
    def process_arrivals(time, runway_controller):
        """
        Main logic loop for arrival simulation
        """
        stats = RunStats.objects.first()

        # 1. Land the planes that are already on the runway from last tick
        set_to_land = Aircraft.objects.filter(zone_status='RUNWAY_LA')
        for plane in set_to_land:
            plane.zone_status = 'LANDED'
            plane.save()
            runway_controller.free_runway(plane, time) # Free the runway
            print(f"Flight {plane.callsign} has landed")
            
            # --- STATS LOGGING ---
            if stats:
                wait_time = (time - plane.queue_entry_time).total_seconds() / 60
                delay_time = (time - plane.scheduled_arrival).total_seconds() / 60

                stats.add_stats(wait_time, 0)
                stats.add_stats(delay_time, 2)
                stats.update_max_arrival_delay(delay_time)
                stats.update_min_arrival_delay(delay_time)

        # 2. Decrease fuel level of all planes in holding pattern by 1 min
        ArrivalManager.decrease_fuel()

        # 3. Get new planes that are arriving and add them to the queue
        arrival_planes = Aircraft.objects.filter(zone_status='SCHEDULED', queue_entry_time__lte=time)
        for plane in arrival_planes:
            # If it doesn't have a departure time, it's an arrival plane
            if plane.scheduled_departure is None:
                plane.zone_status = 'QUEUE_LA' 
                plane.save()

        # 4. Clear planes which have been waiting for longer than 30 minutes, or with not enough fuel
        ArrivalManager.check_divertion(time)

        # 5. Attempt to assign runways based on Priority and Time
        # Filter emergencies and normal planes directly using Django ORM
        emergencies = Aircraft.objects.filter(
            zone_status='QUEUE_LA', 
            emergency_status__in=['MEDICAL', 'MECHANICAL', 'FUEL']
        ).order_by('queue_entry_time')
        
        low_fuel_planes = Aircraft.objects.filter(
            zone_status='QUEUE_LA', 
            emergency_status='NONE', 
            fuel_mins__lte=ArrivalManager.min_fuel_level
        ).order_by('queue_entry_time')
        
        general = Aircraft.objects.filter(
            zone_status='QUEUE_LA', 
            emergency_status='NONE', 
            fuel_mins__gt=ArrivalManager.min_fuel_level
        ).order_by('queue_entry_time')
        
        # Combine them into a strict queue (Emergencies -> Low Fuel -> General)
        queue = list(emergencies) + list(low_fuel_planes) + list(general)

        # Loop through our strictly ordered queue and assign runways
        for plane in queue:
            assigned_runway = runway_controller.assign_runway(plane, time)

            if assigned_runway:
                plane.zone_status = 'RUNWAY_LA'
                plane.save()
                print(f"Flight {plane.callsign} preparing for landing on runway {assigned_runway.bearing}")
            else:
                # Runways are full, stop assigning for this minute
                break