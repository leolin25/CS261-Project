from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from .models import Aircraft, Runway, RunStats
from .arrival_logic import ArrivalController
from .RunwayController import RunwayController


class ArrivalLogicTest(TestCase):

    def setUp(self):
        self.now = timezone.now()

        # Create stats object (used in arrival logic)
        RunStats.objects.create(id=1)

        # Create runway controller
        self.runway_controller = RunwayController(
            landing_duration=45,
            takeoff_duration=45,
            fuel_risk_threshold=20,
            takeoff_risk_threshold=25
        )

        self.arrival_controller = ArrivalController(self.runway_controller)

        # Create runway
        self.runway = Runway.objects.create(
            bearing=9,
            length=3000,
            operating_mode="LANDING",
            operational_status="AVAILABLE",
            occupied_by=None
        )


    # -----------------------------
    # TEST 1: Fuel decreases
    # -----------------------------
    def test_fuel_decreases_each_tick(self):

        plane = Aircraft.objects.create(
            callsign="TEST1",
            zone_status="QUEUE_LA",
            fuel_mins=30,
            last_update=self.now - timedelta(minutes=1),
            altitude=1000
        )

        ArrivalController.update_aircraft_fuel(self.now)

        plane.refresh_from_db()

        self.assertEqual(plane.fuel_mins, 29)


    # -----------------------------
    # TEST 2: Plane diverts when fuel low
    # -----------------------------
    def test_plane_diverts_low_fuel(self):

        plane = Aircraft.objects.create(
            callsign="LOW",
            zone_status="QUEUE_LA",
            fuel_mins=10,
            altitude=2000,
            last_update=self.now
        )

        ArrivalController.update_aircraft_diversions()

        plane.refresh_from_db()

        self.assertEqual(plane.zone_status, "DIVERTED")


    # -----------------------------
    # TEST 3: Altitudes spaced 1000
    # -----------------------------
    def test_altitude_spacing(self):

        Aircraft.objects.create(
            callsign="ALT1",
            zone_status="QUEUE_LA",
            emergency_status="NONE",
            queue_entry_time=self.now,
            last_update=self.now
        )

        Aircraft.objects.create(
            callsign="ALT2",
            zone_status="QUEUE_LA",
            emergency_status="NONE",
            queue_entry_time=self.now + timedelta(seconds=10),
            last_update=self.now
        )

        Aircraft.objects.create(
            callsign="ALT3",
            zone_status="QUEUE_LA",
            emergency_status="NONE",
            queue_entry_time=self.now + timedelta(seconds=20),
            last_update=self.now
        )

        ArrivalController.recalculate_altitudes()

        planes = Aircraft.objects.filter(zone_status="QUEUE_LA").order_by("altitude")

        altitudes = [p.altitude for p in planes]

        self.assertEqual(altitudes, [1000, 2000, 3000])


    # -----------------------------
    # TEST 4: Emergency gets lowest altitude
    # -----------------------------
    def test_emergency_priority_altitude(self):

        Aircraft.objects.create(
            callsign="NORMAL1",
            zone_status="QUEUE_LA",
            emergency_status="NONE",
            queue_entry_time=self.now,
            last_update=self.now
        )

        Aircraft.objects.create(
            callsign="EMERGENCY",
            zone_status="QUEUE_LA",
            emergency_status="MEDICAL",
            queue_entry_time=self.now + timedelta(seconds=10),
            last_update=self.now
        )

        ArrivalController.recalculate_altitudes()

        emergency = Aircraft.objects.get(callsign="EMERGENCY")

        self.assertEqual(emergency.altitude, 1000)


    # -----------------------------
    # TEST 5: Runway assignment
    # -----------------------------
    def test_runway_assignment(self):

        plane = Aircraft.objects.create(
            callsign="LAND1",
            zone_status="QUEUE_LA",
            emergency_status="NONE",
            queue_entry_time=self.now,
            last_update=self.now,
            altitude=1000
        )

        success = self.runway_controller.assign_runway(plane, self.now)

        plane.refresh_from_db()

        self.assertTrue(success)
        self.assertEqual(plane.zone_status, "RUNWAY_LA")


    # -----------------------------
    # TEST 6: Runway free after landing duration
    # -----------------------------
    def test_runway_freed_after_landing(self):

        plane = Aircraft.objects.create(
            callsign="LAND2",
            zone_status="QUEUE_LA",
            emergency_status="NONE",
            queue_entry_time=self.now,
            last_update=self.now,
            altitude=1000
        )

        success = self.runway_controller.assign_runway(plane, self.now)

        self.assertTrue(success)

        plane.refresh_from_db()

        # simulate landing finished
        finished_time = self.now + timedelta(seconds=45)

        freed = self.runway_controller.free_runway(plane, finished_time)

        self.assertTrue(freed)

        plane.refresh_from_db()

        self.assertEqual(plane.zone_status, "LANDED")