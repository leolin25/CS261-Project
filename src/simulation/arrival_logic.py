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

    # Add the new airplane to the back of the queue
    def enqueue(self, airplane):

        # Return False if the queue is full
        if self.length == self.max_length:
            print("queue full")
            return False
            
        self.length += 1
        self.array.append(airplane)
        return True
        
    # Remove the airplane at the front of the queue
    def dequeue(self):
    
        # Return False if the queue is empty
        if self.isEmpty():
            return False

        # Decrease the pointer by 1 when there are airplanes with emergencies
        elif self.priority_pointer > 0:
            self.priority_pointer -= 1
        
        self.length -= 1
        return self.array.pop(0)
        
    # Return the array itself
    def get_array(self):
        return self.array
        
    # Output the items within the queue  
    def output(self):
        print(self.array)
        
    # Look into the first plane in the holding pattern
    def look(self):
        if self.isEmpty():
            return False
        
        return self.array[0]

    # Check if the queue is empty
    def isEmpty(self):
        return self.length == 0

    # Add to the front of the queue because of priority/emergency.
    # If there are planes with emergency already in the queue, add the airplane behind the existing ones 
    def enqueue_priority(self, airplane):
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

"""
This class manages the arrival of planes, including the holding pattern and diverting planes that have been waiting for too long or have low fuel.
"""
class ArrivalManager:
    max_queue_size = 0 
    holding_pattern = Queue()
    
    """
    Divert flights that have waited longer than 30 minutes in the holding pattern, or have fuel <= 11min
    """
    @staticmethod
    def check_divertion(time):
        in_queue = Aircraft.objects.filter(zone_status = 'QUEUE_LA')
        num_diverted_planes = 0 

    
        for i in range(holding_pattern.length):
            wait_duration = (time - holding_pattern.look().queue_entry_time).total_seconds() / 60
            fuel_level = holding_pattern.look().fuel_mins

            # Divert the plane if it has waited for more than 30min, or less or equal to 10min of fuel
            if wait_duration > 30 or fuel_level <= 11:
                plane = holding_pattern.dequeue()
                plane.zone_status = 'DIVERTED'
                plane.save()
                create_flight_stats(plane,time)
                num_diverted_planes += 1
                print(f"Flight {plane.callsign} cancelled")

        return num_diverted_planes
        

    """
    Main logic loop for simulation
    This runs under the assumption that planes take off as soon as they receive a runway slot. 
    """

    '''
    ideally want planes on runway for 45s, but simulation ticks every minute, 
    so this makes planes stay on runway for 60s as planes on the runway are removed every tick.
    free the runway the plane was on.
    '''
    @staticmethod
    def process_arrivals(time,runway_controller):

        # Land the planes that are already on the runway from last tick
        set_to_land = Aircraft.objects.filter(zone_status='RUNWAY_LA')
        for plane in departed:
            plane.zone_status = 'LANDED'
            print(f"Flight {plane.callsign} has landed")
            plane.save()
            runway_controller.free_runway(plane)
            create_flight_stats(plane, time)

        # Get new planes that are on arrival
        arrival_planes = Aircraft.objects.filter(zone_status='SCHEDULED',queue_entry_time__lte=time)
        for plane in ready_to_queue:

            # Check if it is a arrival plane
            if plane.scheduled_departure == None
                plane.zone_status = 'QUEUE_LA' 
                plane.save()

                # Add the planes to the holding pattern
                if plane.emergency_status.choices == "NONE":
                    holding_pattern.enqueue(plane)
                else:
                    holding_pattern.priority_enqueue(plane)
                
        # Keep count of the most number of planes in queue at a time. 
        current_queue_count = Aircraft.objects.filter(zone_status='QUEUE_LA').count()
        if current_queue_count > ArrivalManager.max_planes_in_queue:
            ArrivalManager.max_planes_in_queue=current_queue_count

        # Clear planes which have been waiting for longer than 30 minutes
        ArrivalManager.check_divertion(time)

        # Put the planes on the runway if possible so they can be landed on the next tick
        for i in range(holding_pattern.length):
            assigned_runway = runway_controller.assign_runway(holding_pattern.look())

            if assigned_runway:
                plane = holding_pattern.dequeue()
                plane.zone_status = 'RUNWAY_LA'
                plane.save()
                print(f"Flight {plane.callsign} preparing for landing on runway {assigned_runway.runway_number}")
            else:
                break

    """
    Finding maximum and average delay between scheduled departure time and actual departure time as per requirements
    """
    @staticmethod
    def get_stats():    
        stats = FlightStats.objects.filter(outcome='DEPARTED')

        if not stats.exists():
            return {"peak_queue": ArrivalManager.max_queue_size, "status": "No departures recorded."}
        

        results=  stats.aggregate(
            avg_wait = Avg('takeoff_queue_time_mins'),
            avg_delay = Avg('departure_delay_mins'),
            max_wait = Max('takeoff_queue_time_mins'),
            max_delay = Max('departure_delay_mins')

        )
        results['peak_queue_size'] = ArrivalManager.max_queue_size
        return results
    
    """
    Decrease the fuel level of all planes in the holding pattern by 1 min, this function should be called by main every minute tick
    """
    @staticmethod
    def decrease_fuel():
        holding_pattern = ArrivalManager.holding_pattern
        for plane in holding_pattern.get_array():
            plane.fuel_mins -= 1
            plane.save()