from datetime import timedelta
from .models import Aircraft


"""
This class manages the arrival of planes, including the holding pattern and diverting planes that have been waiting for too long or have low fuel.
"""
class ArrivalController:
    def __init__(self, runway_controller):
        self.runway_controller = runway_controller

    """
    Decrease the fuel level of all planes in the holding pattern by 1 min, this function should be called by main every minute tick
    """
    @staticmethod
    def update_aircraft_fuel(simulation_time):
        aircrafts = Aircraft.objects.filter(zone_status='QUEUE_LA', last_update__lte=simulation_time-timedelta(minutes=1))
        for aircraft in aircrafts:
            aircraft.fuel_mins = max(0, aircraft.fuel_mins - 1)
            aircraft.last_update += timedelta(minutes=1)
        Aircraft.objects.bulk_update(aircrafts, ['fuel_mins', 'last_update'])

    @staticmethod
    def update_aircraft_diversions():
        aircrafts = Aircraft.objects.filter(zone_status='QUEUE_LA', fuel_mins__lte=10)
        for aircraft in aircrafts:
            aircraft.zone_status = 'DIVERTED'
            print(f"Flight {aircraft.callsign} diverted due to low fuel")
        Aircraft.objects.bulk_update(aircrafts, ['zone_status'])

    # """
    # Divert flights that have waited longer than 30 minutes in the holding pattern, or have fuel <= 11min
    # """
    # @staticmethod
    # def check_divertion(time):
    #     num_diverted_planes = 0
    #
    #     # Divert the plane if it has waited for more than 30min
    #     for i in range(ArrivalManager.holding_pattern.length):
    #         wait_duration = (time - ArrivalManager.holding_pattern.look().queue_entry_time).total_seconds() / 60
    #
    #         if wait_duration > 30:
    #             plane = ArrivalManager.holding_pattern.dequeue()
    #             plane.zone_status = 'DIVERTED'
    #             plane.save()
    #             create_flight_stats(plane,time)
    #             num_diverted_planes += 1
    #             print(f"Flight {plane.callsign} diverted due to waiting time")
    #
    #     # Divert planes with not enough fuel
    #     for plane in ArrivalManager.holding_pattern.get_low_fuel_planes(ArrivalManager.min_fuel_level):
    #         plane.zone_status = 'DIVERTED'
    #         plane.save()
    #         create_flight_stats(plane,time)
    #         num_diverted_planes += 1
    #         print(f"Flight {plane.callsign} diverted duel to low fuel")
    #
    #     return num_diverted_planes
    #
    #
    # """
    # Main logic loop for simulation
    # This runs under the assumption that planes take off as soon as they receive a runway slot.
    # """
    #
    # '''
    # ideally want planes on runway for 45s, but simulation ticks every minute,
    # so this makes planes stay on runway for 60s as planes on the runway are removed every tick.
    # free the runway the plane was on.
    # '''
    # @staticmethod
    # def process_arrivals(time,runway_controller):
    #
    #     # Land the planes that are already on the runway from last tick
    #     set_to_land = Aircraft.objects.filter(zone_status='RUNWAY_LA')
    #     for plane in set_to_land:
    #         plane.zone_status = 'LANDED'
    #         print(f"Flight {plane.callsign} has landed")
    #         plane.save()
    #         runway_controller.free_runway(plane)
    #         create_flight_stats(plane, time)
    #
    #     # Decrease fuel level of all planes in holding pattern by 1 min
    #     ArrivalManager.holding_pattern.decrease_fuel_level()
    #
    #     # Get new planes that are on arrival
    #     arrival_planes = Aircraft.objects.filter(zone_status='SCHEDULED',queue_entry_time__lte=time)
    #     for plane in arrival_planes:
    #
    #         # Check if it is a arrival plane
    #         if plane.scheduled_departure == None:
    #             plane.zone_status = 'QUEUE_LA'
    #             plane.save()
    #
    #             # Add the planes to the holding pattern
    #             if plane.emergency_status.choices == "NONE":
    #                 ArrivalManager.holding_pattern.enqueue(plane)
    #             else:
    #                 ArrivalManager.holding_pattern.priority_enqueue(plane)
    #
    #     # Keep count of the most number of planes in queue at a time.
    #     current_queue_count = Aircraft.objects.filter(zone_status='QUEUE_LA').count()
    #     if current_queue_count > ArrivalManager.max_planes_in_queue:
    #         ArrivalManager.max_planes_in_queue=current_queue_count
    #
    #     # Clear planes which have been waiting for longer than 30 minutes, or with not enough fuel
    #     ArrivalManager.check_divertion(time)
    #
    #     # Put the planes on the runway if possible so they can be landed on the next tick
    #     for i in range(ArrivalManager.holding_pattern.length):
    #         assigned_runway = runway_controller.assign_runway(ArrivalManager.holding_pattern.look())
    #
    #         if assigned_runway:
    #             plane = ArrivalManager.holding_pattern.dequeue()
    #             plane.zone_status = 'RUNWAY_LA'
    #             plane.save()
    #             print(f"Flight {plane.callsign} preparing for landing on runway {assigned_runway.runway_number}")
    #         else:
    #             break
