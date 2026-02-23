import os
import django
import sys
from datetime import datetime, timedelta
from django.utils import timezone


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aircraft_model.settings')
django.setup()

from simulation.generation import Generator # Replace with your actual app/file names
from simulation.departure_logic import DepartureManager
from simulation.RunwayController import RunwayController
from simulation.models import Aircraft, Runway, FlightStats

def run_integrated_test():
    # cleanup
    Aircraft.objects.all().delete()
    FlightStats.objects.all().delete()
    Runway.objects.all().delete()

    # setup runway
    Runway.objects.create(runway_number="09R", operating_mode="TAKEOFF", operational_status="AVAILABLE", length=3000, bearing=90)
    controller = RunwayController()

    # generate the flights from csv data
    print("--- Loading data from CSV and generating schedule ---")
    # generating x hours of flights, y per hour
    gen = Generator(hour_limit=2, inbound_per_hour=0, outbound_per_hour=60)
    inbound, outbound = gen.run_generation()
    
    # save the generated aircraft to the database
    for plane in outbound:
        Aircraft.objects.update_or_create(
            callsign=plane.callsign, 
            defaults={
                'zone_status': plane.zone_status,
                'queue_entry_time': plane.queue_entry_time,
                'scheduled_departure': plane.scheduled_departure,
                'operator': plane.operator
            }
        )

    # run the simulation loop 
    start_time = timezone.now()
    sim_time = start_time
    print(f"--- Starting Simulation at {sim_time.strftime('%H:%M')} ---")

    for tick in range(180): # 180 minutes = 3 hours
        DepartureManager.process_departures(sim_time, controller)
        sim_time += timedelta(minutes=1)

    # stats report
    print("\n" + "="*30)
    print("FINAL SIMULATION REPORT")
    print("="*30)
    stats = DepartureManager.get_stats()
    for key, value in stats.items():
        print(f"{key.replace('_', ' ').title()}: {value}")

if __name__ == "__main__":
    run_integrated_test()