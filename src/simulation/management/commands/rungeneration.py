from django.core.management.base import BaseCommand
from simulation.generation import Generator


class Command(BaseCommand):
    help = "Execute a sample run of aircraft generation"

    def add_arguments(self, parser):
        parser.add_argument("hour_limit", type=int, default=12, nargs="?")
        parser.add_argument("inbound_per_hour", type=int, default=15, nargs="?")
        parser.add_argument("outbound_per_hour", type=int, default=15, nargs="?")

    def handle(self, *args, **options):
        generator = Generator(
            hour_limit=options["hour_limit"],
            inbound_per_hour=options["inbound_per_hour"],
            outbound_per_hour=options["outbound_per_hour"],
        )
        for _ in range(10):
            plane = generator.generate_aircraft(is_arrival=True)
            self.stdout.write(f"Generated Aircraft: {plane.callsign}, Scheduled Arrival: {plane.scheduled_arrival}, Queue Entry: {plane.queue_entry_time}, Fuel: {plane.fuel_mins} mins")