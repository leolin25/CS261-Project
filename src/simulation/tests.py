from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from .models import Aircraft, Runway
from .generation import Generator
from .RunwayController import RunwayController
from .departure_logic import DepartureController
from .arrival_logic import ArrivalManager
from .control import Controller


# ---------------------------
# Generator Tests
# ---------------------------
class GeneratorTest(TestCase):

    def test_generate_arrival_aircraft(self):
        generator = Generator(hour_limit=2, inbound_per_hour=2, outbound_per_hour=2)

        aircraft = generator.generate_aircraft(is_arrival=True)

        self.assertIsNotNone(aircraft.scheduled_arrival)
        self.assertIsNone(aircraft.scheduled_departure)
        self.assertEqual(aircraft.zone_status, "SCHEDULED")


# ---------------------------
# Runway Logic Tests
# ---------------------------
class RunwayLogicTest(TestCase):

    def setUp(self):
        self.rc = RunwayController(
            landing_duration=45,
            takeoff_duration=60,
            fuel_risk_threshold=20,
            takeoff_risk_threshold=25
        )
        self.now = timezone.now()

    def test_runway_assignment_and_timing(self):
        """Tests landing runway occupancy timing."""

        runway = Runway.objects.create(
            bearing=9,
            length=3000,
            operating_mode="LANDING",   # ensure valid runway for landing
            operational_status="AVAILABLE",
            occupied_by=None
        )
        runway.save()

        plane = Aircraft.objects.create(
            callsign="TEST45",
            zone_status="QUEUE_LA",
            scheduled_arrival=self.now,
            queue_entry_time=self.now - timedelta(minutes=1)  # must be earlier
        )
        plane.save()

        # Assign runway
        success = self.rc.assign_runway(plane, self.now)
        self.assertTrue(success)

        plane.refresh_from_db()
        runway.refresh_from_db()

        self.assertEqual(plane.zone_status, "RUNWAY_LA")
        self.assertEqual(runway.occupied_by, plane)

        # Try freeing runway too early
        self.assertFalse(
            self.rc.free_runway(plane, self.now + timedelta(seconds=30))
        )

        # Free runway after enough time
        self.assertTrue(
            self.rc.free_runway(plane, self.now + timedelta(seconds=50))
        )

        plane.refresh_from_db()
        runway.refresh_from_db()

        self.assertEqual(plane.zone_status, "LANDED")
        self.assertIsNone(runway.occupied_by)


# ---------------------------
# Controller Status Tests
# ---------------------------
class ControllerStatusTest(TestCase):

    def test_update_aircraft_status(self):
        now = timezone.now()

        aircraft = Aircraft.objects.create(
            callsign="TEST2",
            scheduled_departure=now,
            zone_status="SCHEDULED",
            queue_entry_time=now
        )
        aircraft.save()

        controller = Controller(
            runways=1,
            inbound_per_hour=1,
            outbound_per_hour=1
        )

        controller.simulation_time = now

        controller.update_aircraft_statuses()

        aircraft.refresh_from_db()

        self.assertEqual(aircraft.zone_status, "QUEUE_TO")


# ---------------------------
# Arrival Queue Tests
# ---------------------------
class ArrivalQueueTest(TestCase):

    def setUp(self):
        # Reset holding pattern queue if implementation uses a static instance
        try:
            ArrivalManager.holding_pattern.queue.clear()
        except:
            pass

    def test_enqueue_and_dequeue(self):

        plane = Aircraft.objects.create(
            callsign="ARR1",
            zone_status="QUEUE_LA",
            fuel_mins=30,
            queue_entry_time=timezone.now()
        )

        ArrivalManager.holding_pattern.enqueue(plane)

        self.assertEqual(
            ArrivalManager.holding_pattern.length,
            1
        )

        removed = ArrivalManager.holding_pattern.dequeue()

        self.assertEqual(removed.callsign, "ARR1")