import random
from datetime import timedelta
from django.db.models import Avg, Max
from .models import Aircraft
from .logic import create_flight_stats


class Queue:
    """A queue data structure"""
    
    def __init__(self):
        self.length = 0
        self.array = []
        self.priority_pointer = 0 # This points to the index position that the new emergency plane should be placed in

    # Add the new airplane to the back of the queue
    def enqueue(self, airplane):
        self.length += 1
        self.array.append(airplane)
        
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

        self.array.insert(self.priority_pointer, airplane)
        self.priority_pointer += 1
        self.length += 1

    # Decrease the fuel level at each tick
    def decrease_fuel_level(self):
        for plane in self.array:
            plane.fuel_mins -= 1
            plane.save()

    # Return a list of planes that have fuel level below a threshold 
    def get_low_fuel_planes(self, min_fuel):
        index = 0
        output_list = []

        # Check all planes if they have low fuel
        while index < self.length:

            # Remove the plane from the queue if the fuel is too low
            if self.array[index].fuel_mins <= min_fuel:
                output_list.append(self.array.pop(index))
                self.length -= 1
            else:
                index += 1
        
        return output_list

"""
This class manages the arrival of planes, including the holding pattern and diverting planes that have been waiting for too long or have low fuel.
"""
class ArrivalManager:
    max_planes_in_queue = 0 
    holding_pattern = Queue()
    min_fuel_level = 11 # Minimum fuel level before diverting
    
    """
    Divert flights that have waited longer than 30 minutes in the holding pattern, or have fuel <= 11min
    """
    @staticmethod
    def check_divertion(time):
        num_diverted_planes = 0 

        # Divert the plane if it has waited for more than 30min
        for i in range(ArrivalManager.holding_pattern.length):
            wait_duration = (time - ArrivalManager.holding_pattern.look().queue_entry_time).total_seconds() / 60

            if wait_duration > 30:
                plane = ArrivalManager.holding_pattern.dequeue()
                plane.zone_status = 'DIVERTED'
                plane.save()
                create_flight_stats(plane,time)
                num_diverted_planes += 1
                print(f"Flight {plane.callsign} diverted due to waiting time")

        # Divert planes with not enough fuel
        for plane in ArrivalManager.holding_pattern.get_low_fuel_planes(ArrivalManager.min_fuel_level):
            plane.zone_status = 'DIVERTED'
            plane.save()
            create_flight_stats(plane,time)
            num_diverted_planes += 1
            print(f"Flight {plane.callsign} diverted duel to low fuel")

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
        for plane in set_to_land:
            plane.zone_status = 'LANDED'
            print(f"Flight {plane.callsign} has landed")
            plane.save()
            runway_controller.free_runway(plane)
            create_flight_stats(plane, time)

        # Decrease fuel level of all planes in holding pattern by 1 min
        ArrivalManager.holding_pattern.decrease_fuel_level()

        # Get new planes that are on arrival
        arrival_planes = Aircraft.objects.filter(zone_status='SCHEDULED',queue_entry_time__lte=time)
        for plane in arrival_planes:

            # Check if it is a arrival plane
            if plane.scheduled_departure == None:
                plane.zone_status = 'QUEUE_LA' 
                plane.save()

                # Add the planes to the holding pattern
                if plane.emergency_status.choices == "NONE":
                    ArrivalManager.holding_pattern.enqueue(plane)
                else:
                    ArrivalManager.holding_pattern.enqueue_priority(plane)
                
        # Keep count of the most number of planes in queue at a time. 
        current_queue_count = Aircraft.objects.filter(zone_status='QUEUE_LA').count()
        if current_queue_count > ArrivalManager.max_planes_in_queue:
            ArrivalManager.max_planes_in_queue=current_queue_count

        # Clear planes which have been waiting for longer than 30 minutes, or with not enough fuel
        ArrivalManager.check_divertion(time)

        # Put the planes on the runway if possible so they can be landed on the next tick
        for i in range(ArrivalManager.holding_pattern.length):
            assigned_runway = runway_controller.assign_runway(ArrivalManager.holding_pattern.look())

            if assigned_runway:
                plane = ArrivalManager.holding_pattern.dequeue()
                plane.zone_status = 'RUNWAY_LA'
                plane.save()
                print(f"Flight {plane.callsign} preparing for landing on runway {assigned_runway.runway_number}")
            else:
                break
    
    """
    Decrease the fuel level of all planes in the holding pattern by 1 min, this function should be called by main every minute tick
    """
    @staticmethod
    def decrease_fuel():
        holding_pattern = ArrivalManager.holding_pattern
        for plane in holding_pattern.get_array():
            plane.fuel_mins -= 1
            plane.save()
