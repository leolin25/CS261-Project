import random
from datetime import timedelta
from django.db.models import Avg, Max
from .models import Aircraft, FlightStats
from .logic import create_flight_stats


class Stack():
    """A stack data structure"""
    
    def __init__(self):
        self.length = 0
        self.array = []
        
    def enqueue(self, airplane):
        self.length += 1
        self.array.append(airplane)

    def dequeue(self):
        if self.length == 0:
            return False
        
        self.length -= 1
        
        return self.array.pop(0)

    def get_array(self):
        return self.array
    
    def output(self):
        print(self.array)

    


class ArrivalManager:
    max_queue_size = 0 
    holding_pattern_stack = 

  
    """Applying normal distribution for queue entry
    Mean = Scheduled departure time
    S.D = 5m
    """
    @staticmethod
    def entry_variance(plane):
        if plane.scheduled_departure and not plane.queue_entry_time:
            variance = random.gauss(0,5) 
            plane.queue_entry_time = plane.scheduled_departure+timedelta(minutes=variance)
            plane.save()
        return plane
    
    """
    Divert flights that have waited longer than 30 minutes in the holding pattern
    """
    @staticmethod
    def check_divertion(time):
        in_queue = Aircraft.objects.filter(zone_status = 'QUEUE_LA')
        num_diverted_planes = 0 
      
        for plane in in_queue:
            wait_duration = (time - plane.queue_entry_time).total_seconds() / 60
            
            if wait_duration>30:
                plane.zone_status = 'DIVERTED'
                plane.save()
                create_flight_stats(plane,time)
                num_diverted_planes += 1
                print(f"Flight {plane.callsign} cancelled")

        return num_diverted_planes

  
    def check_holding_pattern(plane):
        in_queue = Aircraft.objects.filter(zone_status = 'QUEUE_LA')
        


  
    """
    Main logic loop for simulation
    This runs under the assumption that planes take off as soon as they receive a runway slot. 
    """
    @staticmethod
    def process_arrivals(time,runway_controller):
        scheduled_flights = Aircraft.objects.filter(zone_status='SCHEDULED',scheduled_departure__isnull=False)

        #Place scheduled planes in the queue if possible
        for plane in scheduled_flights:
            plane = DepartureManager.entry_variance(plane)
            if time>=plane.queue_entry_time:
                plane.zone_status = 'QUEUE_TO'
                plane.save()
                
        # Keep count of the most number of planes in queue at a time. 
        current_queue_count = Aircraft.objects.filter(zone_status='QUEUE_TO').count()
        if current_queue_count > DepartureManager.max_queue_size:
            DepartureManager.max_queue_size=current_queue_count

        #Clear planes which have been waiting for longer than 30 minutes
        DepartureManager.check_cancellations(time)

        #Attempt to assign runways to planes in queue, ensuring FIFO ordering
        queue = Aircraft.objects.filter(zone_status='QUEUE_TO').order_by('queue_entry_time')

        for plane in queue:
            assigned_runway = runway_controller.assign_runway(plane)

            if assigned_runway:
                plane.zone_status = 'DEPARTED'
                plane.save()
                create_flight_stats(plane,time)
                print(f"Flight {plane.callsign} taking off on Runway {assigned_runway.runway_number}")
        


    """
    Finding maximum and average delay between scheduled departure time and actual departure time as per requirements
    """
    @staticmethod
    def get_stats():    
        stats = FlightStats.objects.filter(outcome='DEPARTED')

        if not stats.exists():
            return {"peak_queue": DepartureManager.max_queue_size, "status": "No departures recorded."}
        

        results=  stats.aggregate(
            avg_wait = Avg('takeoff_queue_time_mins'),
            avg_delay = Avg('departure_delay_mins'),
            max_wait = Max('takeoff_queue_time_mins'),
            max_delay = Max('departure_delay_mins')

        )
        results['peak_queue_size'] = DepartureManager.max_queue_size
        return results
