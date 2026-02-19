from django.core.management.base import BaseCommand
from simulation.generation import Generator


class Command(BaseCommand):
    help = "Execute a sample run of aircraft generation"

    def add_arguments(self, parser):
        parser.add_argument("hour_limit", type=int, default=12, nargs="?")
        parser.add_argument("inbound_per_hour", type=int, default=15, nargs="?")
        parser.add_argument("outbound_per_hour", type=int, default=15, nargs="?")

    def output_schedule(self, arrivals, departures):
        self.stdout.write("-----------------Arrivals Schedule-----------------")
        for aircraft in arrivals:
            self.stdout.write(f"Aircraft: {aircraft.callsign} Scheduled: {aircraft.scheduled_arrival} Expected: {aircraft.queue_entry_time}")

        self.stdout.write("-----------------Departures Schedule-----------------")
        for aircraft in departures:
            self.stdout.write(f"Aircraft: {aircraft.callsign} Scheduled: {aircraft.scheduled_departure} Expected: {aircraft.queue_entry_time}")

    def handle(self, *args, **options):
        generator = Generator(
            hour_limit=options["hour_limit"],
            inbound_per_hour=options["inbound_per_hour"],
            outbound_per_hour=options["outbound_per_hour"],
        )
        arrivals, departures = generator.run_generation()
        self.output_schedule(arrivals, departures)
