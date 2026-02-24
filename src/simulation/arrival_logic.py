import random
from datetime import timedelta
from django.db.models import Avg, Max
from .models import Aircraft, FlightStats
from .logic import create_flight_stats


class Queue:
    """A queue data structure"""
    
    def __init__(self):
        self.length = 0
        self.array = []
        self.priority_pointer = 0 # This points to the index position that the new emergency plane should be placed in
        self.max_length = 4 # Maximum number of planes in the holding pattern
        
    def enqueue(self, airplane):
        #Add the new airplane to the back of the queue

        # Return False if the queue is full
        if self.length == self.max_length:
            print("queue full")
            return False
        else:
            self.length += 1
            self.array.append(airplane)

            return True

    def dequeue(self):
        #Remove the airplane at the front of the queue

        # Return False if the queue is empty
        if self.length == 0:
            return False

        # Decrease the pointer by 1 when there are airplanes with emergencies
        elif self.priority_pointer > 0:
            self.priority_pointer -= 1
        
        self.length -= 1
        return self.array.pop(0)

    def get_array(self):
        #Return the array itself
        
        return self.array
    
    def output(self):
        #Output the items within the queue

        print(self.array)

    def enqueue_priority(self, airplane):
        #Add to the front of the queue because of priority/emergency.
        #If there are planes with emergency already in the queue, add the airplane behind the existing ones

        last_plane = True # Return True if enqueue successful, this will be replaced with the plane that got kicked out if the queue is full
        
        # If hold pattern full of emergency, return False
        if self.priority_pointer == self.max_length:
            print("priority full")
            return False
        
        # If full, remove the last plane and add the emergency plane to the front
        elif self.length == self.max_length:
            last_plane = self.array.pop(-1)
            print("This one got kicked out:", last_plane)
            self.length -= 1

        self.array.insert(self.priority_pointer, airplane)
        self.priority_pointer += 1
        self.length += 1

        return last_plane

    


class ArrivalManager:
    max_queue_size = 0 
    holding_pattern_stack = Stack()
    
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
