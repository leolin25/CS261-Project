import random
from datetime import timedelta
from django.db.models import Avg, Max
from .models import Aircraft, FlightStats
from .logic import create_flight_stats

class ArrivalManager:
    # Tracks the highest number of planes in the holding pattern at once
    max_planes_in_queue = 0 
    
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

        for plane in in_queue:
            wait_duration = (time - plane.queue_entry_time).total_seconds() / 60

            # Divert if wait is > 30mins OR fuel is critically low
            if wait_duration > 30 or plane.fuel_mins <= ArrivalManager.min_fuel_level:
                plane.zone_status = 'DIVERTED'
                plane.save()
                create_flight_stats(plane, time)
                num_diverted_planes += 1
                
                reason = "waiting time" if wait_duration > 30 else "low fuel"
                print(f"Flight {plane.callsign} diverted due to {reason}")

        return num_diverted_planes
        
    @staticmethod
    def decrease_fuel():
        """
        Decrease the fuel level of all planes in the holding pattern by 1 min.
        """
        in_queue = Aircraft.objects.filter(zone_status='QUEUE_LA')
        for plane in in_queue:
            plane.fuel_mins -= 1
            plane.save()

    @staticmethod
    def process_arrivals(time, runway_controller):
        """
        Main logic loop for arrival simulation
        """
        # 1. Land the planes that are already on the runway from last tick
        set_to_land = Aircraft.objects.filter(zone_status='RUNWAY_LA')
        for plane in set_to_land:
            plane.zone_status = 'LANDED'
            print(f"Flight {plane.callsign} has landed")
            plane.save()
            runway_controller.free_runway(plane)
            create_flight_stats(plane, time)

        # 2. Decrease fuel level of all planes in holding pattern by 1 min
        ArrivalManager.decrease_fuel()

        # 3. Get new planes that are arriving and add them to the queue
        arrival_planes = Aircraft.objects.filter(zone_status='SCHEDULED', queue_entry_time__lte=time)
        for plane in arrival_planes:
            # If it doesn't have a departure time, it's an arrival plane
            if plane.scheduled_departure is None:
                plane.zone_status = 'QUEUE_LA' 
                plane.save()
                
        # 4. Keep count of the most number of planes in queue at a time. 
        current_queue_count = Aircraft.objects.filter(zone_status='QUEUE_LA').count()
        if current_queue_count > ArrivalManager.max_planes_in_queue:
            ArrivalManager.max_planes_in_queue = current_queue_count

        # 5. Clear planes which have been waiting for longer than 30 minutes, or with not enough fuel
        ArrivalManager.check_divertion(time)

        # 6. Attempt to assign runways based on Priority and Time
        # Pull all queued planes into a list so we can sort them by priority
        queue = list(Aircraft.objects.filter(zone_status='QUEUE_LA'))
        
        # Sort logic: Emergencies/Low Fuel get priority tier '0'. Normal planes get tier '1'.
        # Within the same tier, planes are sorted by their queue_entry_time (First In, First Out)
        queue.sort(key=lambda p: (
            0 if p.emergency_status != 'NONE' or p.fuel_mins <= ArrivalManager.min_fuel_level else 1,
            p.queue_entry_time
        ))

        # Loop through our strictly ordered queue and assign runways
        for plane in queue:
            assigned_runway = runway_controller.assign_runway(plane)

            if assigned_runway:
                plane.zone_status = 'RUNWAY_LA'
                plane.save()
                print(f"Flight {plane.callsign} preparing for landing on runway {assigned_runway.runway_number}")
            else:
                # Runways are full, stop assigning for this minute
                break

    @staticmethod
    def get_stats():    
        """
        Finding maximum and average delay between scheduled arrival time and actual arrival time
        """
        stats = FlightStats.objects.filter(outcome='LANDED')

        if not stats.exists():
            return {"peak_queue": ArrivalManager.max_planes_in_queue, "status": "No arrivals recorded."}
        
        results = stats.aggregate(
            avg_wait = Avg('holding_time_mins'),
            avg_delay = Avg('arrival_delay_mins'),
            max_wait = Max('holding_time_mins'),
            max_delay = Max('arrival_delay_mins')
        )
        
        results['peak_queue_size'] = ArrivalManager.max_planes_in_queue
        return results