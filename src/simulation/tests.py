from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
import math

from .models import Aircraft, Runway, RunStats, RunConfig
from .arrival_logic import ArrivalController
from .departure_logic import DepartureController
from .RunwayController import RunwayController
from .generation import Generator
from .control import Controller


# ============================================================
# HELPERS
# ============================================================

def make_aircraft(**kwargs):
    defaults = dict(
        callsign="TEST",
        operator="TST",
        origin="LHR",
        destination="JFK",
        zone_status="SCHEDULED",
        emergency_status="NONE",
        altitude=0,
        fuel_mins=60,
        last_update=timezone.now(),
    )
    defaults.update(kwargs)
    return Aircraft.objects.create(**defaults)


def make_runway(**kwargs):
    defaults = dict(
        bearing=9,
        length=3000,
        operating_mode="MIXED",
        operational_status="AVAILABLE",
        occupied_by=None,
    )
    defaults.update(kwargs)
    return Runway.objects.create(**defaults)


def make_runway_controller():
    return RunwayController(
        landing_duration=45,
        takeoff_duration=45,
        fuel_risk_threshold=20,
        takeoff_risk_threshold=25,
    )


def make_config(**kwargs):
    defaults = dict(
        runways=2,
        runways_mixed=2,
        runways_takeoff=0,
        runways_landing=0,
        inbound_per_hour=10,
        outbound_per_hour=10,
        timescale=60,
        schedule_limit=2,
        max_wait=60,
        landing_duration=45,
        takeoff_duration=45,
        fuel_risk_threshold=20,
        takeoff_risk_threshold=25,
        random_events=False,
        stop=False,
    )
    defaults.update(kwargs)
    return RunConfig.objects.create(**defaults)


# ============================================================
# ARRIVAL CONTROLLER TESTS
# ============================================================

class ArrivalFuelTests(TestCase):

    def setUp(self):
        self.now = timezone.now()
        RunStats.objects.create(id=1)

    def test_fuel_decreases_each_tick(self):
        plane = make_aircraft(
            callsign="FUEL1",
            zone_status="QUEUE_LA",
            fuel_mins=30,
            last_update=self.now - timedelta(minutes=1),
            altitude=1000,
        )
        ArrivalController.update_aircraft_fuel(self.now)
        plane.refresh_from_db()
        self.assertEqual(plane.fuel_mins, 29)

    def test_fuel_does_not_go_below_zero(self):
        plane = make_aircraft(
            callsign="FUEL2",
            zone_status="QUEUE_LA",
            fuel_mins=0,
            last_update=self.now - timedelta(minutes=1),
            altitude=1000,
        )
        ArrivalController.update_aircraft_fuel(self.now)
        plane.refresh_from_db()
        self.assertEqual(plane.fuel_mins, 0)

    def test_fuel_not_decremented_if_not_due(self):
        # last_update is only 30 seconds ago, not a full minute
        plane = make_aircraft(
            callsign="FUEL3",
            zone_status="QUEUE_LA",
            fuel_mins=30,
            last_update=self.now - timedelta(seconds=30),
            altitude=1000,
        )
        ArrivalController.update_aircraft_fuel(self.now)
        plane.refresh_from_db()
        self.assertEqual(plane.fuel_mins, 30)

    def test_fuel_only_decremented_for_queue_la(self):
        # Plane in departure queue should not have fuel decremented
        plane = make_aircraft(
            callsign="FUEL4",
            zone_status="QUEUE_TO",
            fuel_mins=30,
            last_update=self.now - timedelta(minutes=1),
        )
        ArrivalController.update_aircraft_fuel(self.now)
        plane.refresh_from_db()
        self.assertEqual(plane.fuel_mins, 30)


class ArrivalDiversionTests(TestCase):

    def setUp(self):
        self.now = timezone.now()
        RunStats.objects.create(id=1)

    def test_plane_diverts_at_threshold(self):
        plane = make_aircraft(
            callsign="DIV1",
            zone_status="QUEUE_LA",
            fuel_mins=10,
            altitude=2000,
            last_update=self.now,
        )
        ArrivalController.update_aircraft_diversions()
        plane.refresh_from_db()
        self.assertEqual(plane.zone_status, "DIVERTED")

    def test_plane_does_not_divert_above_threshold(self):
        plane = make_aircraft(
            callsign="DIV2",
            zone_status="QUEUE_LA",
            fuel_mins=11,
            altitude=2000,
            last_update=self.now,
        )
        ArrivalController.update_aircraft_diversions()
        plane.refresh_from_db()
        self.assertEqual(plane.zone_status, "QUEUE_LA")

    def test_diversion_resets_altitude(self):
        plane = make_aircraft(
            callsign="DIV3",
            zone_status="QUEUE_LA",
            fuel_mins=5,
            altitude=3000,
            last_update=self.now,
        )
        ArrivalController.update_aircraft_diversions()
        plane.refresh_from_db()
        self.assertEqual(plane.altitude, 0)

    def test_diversion_updates_max_diverted_stat(self):
        make_aircraft(
            callsign="DIV4",
            zone_status="QUEUE_LA",
            fuel_mins=5,
            altitude=1000,
            last_update=self.now,
        )
        ArrivalController.update_aircraft_diversions()
        stats = RunStats.objects.first()
        self.assertGreaterEqual(stats.max_num_diverted, 1)


class ArrivalAltitudeTests(TestCase):

    def setUp(self):
        self.now = timezone.now()
        RunStats.objects.create(id=1)

    def test_altitude_spacing(self):
        for i in range(3):
            make_aircraft(
                callsign=f"ALT{i}",
                zone_status="QUEUE_LA",
                emergency_status="NONE",
                queue_entry_time=self.now + timedelta(seconds=i * 10),
                last_update=self.now,
            )
        ArrivalController.recalculate_altitudes()
        altitudes = list(
            Aircraft.objects.filter(zone_status="QUEUE_LA")
            .order_by("altitude")
            .values_list("altitude", flat=True)
        )
        self.assertEqual(altitudes, [1000, 2000, 3000])

    def test_emergency_gets_lowest_altitude(self):
        make_aircraft(
            callsign="NORMAL1",
            zone_status="QUEUE_LA",
            emergency_status="NONE",
            queue_entry_time=self.now,
            last_update=self.now,
        )
        make_aircraft(
            callsign="EMERG1",
            zone_status="QUEUE_LA",
            emergency_status="MEDICAL",
            queue_entry_time=self.now + timedelta(seconds=10),
            last_update=self.now,
        )
        ArrivalController.recalculate_altitudes()
        emergency = Aircraft.objects.get(callsign="EMERG1")
        self.assertEqual(emergency.altitude, 1000)

    def test_multiple_emergencies_sorted_by_entry_time(self):
        make_aircraft(
            callsign="E1",
            zone_status="QUEUE_LA",
            emergency_status="FUEL",
            queue_entry_time=self.now,
            last_update=self.now,
        )
        make_aircraft(
            callsign="E2",
            zone_status="QUEUE_LA",
            emergency_status="MECHANICAL",
            queue_entry_time=self.now + timedelta(seconds=5),
            last_update=self.now,
        )
        ArrivalController.recalculate_altitudes()
        e1 = Aircraft.objects.get(callsign="E1")
        e2 = Aircraft.objects.get(callsign="E2")
        self.assertLess(e1.altitude, e2.altitude)

    def test_altitudes_recalculated_after_diversion(self):
        # Three planes in stack, one diverts — remaining two should close the gap
        for i in range(3):
            make_aircraft(
                callsign=f"GAP{i}",
                zone_status="QUEUE_LA",
                emergency_status="NONE",
                fuel_mins=5 if i == 1 else 50,
                queue_entry_time=self.now + timedelta(seconds=i * 10),
                last_update=self.now,
                altitude=(i + 1) * 1000,
            )
        ArrivalController.update_aircraft_diversions()
        remaining = Aircraft.objects.filter(zone_status="QUEUE_LA").order_by("altitude")
        altitudes = [p.altitude for p in remaining]
        self.assertEqual(altitudes, [1000, 2000])


# ============================================================
# DEPARTURE CONTROLLER TESTS
# ============================================================

class DepartureCancellationTests(TestCase):

    def setUp(self):
        self.now = timezone.now()
        RunStats.objects.create(id=1)
        self.runway_controller = make_runway_controller()
        self.departure_controller = DepartureController(self.runway_controller, max_wait=30)

    def test_aircraft_cancelled_after_max_wait(self):
        plane = make_aircraft(
            callsign="CANC1",
            zone_status="QUEUE_TO",
            queue_entry_time=self.now - timedelta(minutes=31),
            last_update=self.now,
        )
        self.departure_controller.update_aircraft_cancellations(self.now)
        plane.refresh_from_db()
        self.assertEqual(plane.zone_status, "CANCELLED")

    def test_aircraft_not_cancelled_before_max_wait(self):
        plane = make_aircraft(
            callsign="CANC2",
            zone_status="QUEUE_TO",
            queue_entry_time=self.now - timedelta(minutes=20),
            last_update=self.now,
        )
        self.departure_controller.update_aircraft_cancellations(self.now)
        plane.refresh_from_db()
        self.assertEqual(plane.zone_status, "QUEUE_TO")

    def test_cancellation_count_returned(self):
        for i in range(3):
            make_aircraft(
                callsign=f"CANC{i+3}",
                zone_status="QUEUE_TO",
                queue_entry_time=self.now - timedelta(minutes=60),
                last_update=self.now,
            )
        count = self.departure_controller.update_aircraft_cancellations(self.now)
        self.assertEqual(count, 3)

    def test_cancellation_updates_max_cancelled_stat(self):
        make_aircraft(
            callsign="CANC6",
            zone_status="QUEUE_TO",
            queue_entry_time=self.now - timedelta(minutes=60),
            last_update=self.now,
        )
        self.departure_controller.update_aircraft_cancellations(self.now)
        stats = RunStats.objects.first()
        self.assertGreaterEqual(stats.max_num_cancelled, 1)


class DepartureProcessingTests(TestCase):

    def setUp(self):
        self.now = timezone.now()
        RunStats.objects.create(id=1)
        self.runway_controller = make_runway_controller()
        self.departure_controller = DepartureController(self.runway_controller, max_wait=60)
        make_runway(operating_mode="TAKEOFF")

    def test_aircraft_assigned_runway_for_takeoff(self):
        plane = make_aircraft(
            callsign="DEP1",
            zone_status="QUEUE_TO",
            queue_entry_time=self.now,
            scheduled_departure=self.now,
            last_update=self.now,
        )
        self.departure_controller.process_departures(self.now)
        plane.refresh_from_db()
        self.assertEqual(plane.zone_status, "RUNWAY_TO")

    def test_aircraft_departs_after_takeoff_duration(self):
        plane = make_aircraft(
            callsign="DEP2",
            zone_status="QUEUE_TO",
            queue_entry_time=self.now,
            scheduled_departure=self.now,
            last_update=self.now,
        )
        self.departure_controller.process_departures(self.now)
        plane.refresh_from_db()
        finished_time = self.now + timedelta(seconds=45)
        self.departure_controller.process_departures(finished_time)
        plane.refresh_from_db()
        self.assertEqual(plane.zone_status, "DEPARTED")

    def test_fifo_ordering(self):
        # First plane in queue should be assigned runway before second
        early = make_aircraft(
            callsign="EARLY",
            zone_status="QUEUE_TO",
            queue_entry_time=self.now - timedelta(minutes=10),
            scheduled_departure=self.now,
            last_update=self.now,
        )
        late = make_aircraft(
            callsign="LATE",
            zone_status="QUEUE_TO",
            queue_entry_time=self.now,
            scheduled_departure=self.now,
            last_update=self.now,
        )
        self.departure_controller.process_departures(self.now)
        early.refresh_from_db()
        late.refresh_from_db()
        self.assertEqual(early.zone_status, "RUNWAY_TO")
        self.assertEqual(late.zone_status, "QUEUE_TO")

    def test_departure_stats_recorded(self):
        plane = make_aircraft(
            callsign="DEP3",
            zone_status="QUEUE_TO",
            queue_entry_time=self.now - timedelta(minutes=5),
            scheduled_departure=self.now - timedelta(minutes=5),
            last_update=self.now,
        )
        self.departure_controller.process_departures(self.now)
        plane.refresh_from_db()
        finished_time = self.now + timedelta(seconds=45)
        self.departure_controller.process_departures(finished_time)
        stats = RunStats.objects.first()
        self.assertGreater(stats.sum_takeoff_queue_time_mins, 0)


# ============================================================
# RUNWAY CONTROLLER TESTS
# ============================================================

class RunwayAssignmentTests(TestCase):

    def setUp(self):
        self.now = timezone.now()
        self.runway_controller = make_runway_controller()

    def test_landing_runway_assigned(self):
        make_runway(operating_mode="LANDING")
        plane = make_aircraft(callsign="RWY1", zone_status="QUEUE_LA", altitude=1000)
        success = self.runway_controller.assign_runway(plane, self.now)
        plane.refresh_from_db()
        self.assertTrue(success)
        self.assertEqual(plane.zone_status, "RUNWAY_LA")

    def test_takeoff_runway_assigned(self):
        make_runway(operating_mode="TAKEOFF")
        plane = make_aircraft(
            callsign="RWY2",
            zone_status="QUEUE_TO",
            scheduled_departure=self.now,
        )
        success = self.runway_controller.assign_runway(plane, self.now)
        plane.refresh_from_db()
        self.assertTrue(success)
        self.assertEqual(plane.zone_status, "RUNWAY_TO")

    def test_mixed_runway_assigned_after_optimisation(self):
        make_runway(operating_mode="MIXED")
        plane = make_aircraft(callsign="RWY3", zone_status="QUEUE_LA", altitude=1000)
        # Optimise first so mixed becomes LANDING
        self.runway_controller.optimise_runway_mode(self.now)
        success = self.runway_controller.assign_runway(plane, self.now)
        self.assertTrue(success)

    def test_no_runway_available_returns_false(self):
        # No runways created
        plane = make_aircraft(callsign="RWY4", zone_status="QUEUE_LA", altitude=1000)
        success = self.runway_controller.assign_runway(plane, self.now)
        self.assertFalse(success)

    def test_occupied_runway_not_reassigned(self):
        runway = make_runway(operating_mode="LANDING")
        occupant = make_aircraft(callsign="OCC1", zone_status="RUNWAY_LA")
        runway.occupied_by = occupant
        runway.operational_status = "OCCUPIED"
        runway.save()
        new_plane = make_aircraft(callsign="OCC2", zone_status="QUEUE_LA", altitude=1000)
        success = self.runway_controller.assign_runway(new_plane, self.now)
        self.assertFalse(success)

    def test_runway_freed_after_landing_duration(self):
        make_runway(operating_mode="LANDING")
        plane = make_aircraft(callsign="FREE1", zone_status="QUEUE_LA", altitude=1000)
        self.runway_controller.assign_runway(plane, self.now)
        plane.refresh_from_db()
        freed = self.runway_controller.free_runway(plane, self.now + timedelta(seconds=45))
        self.assertTrue(freed)
        plane.refresh_from_db()
        self.assertEqual(plane.zone_status, "LANDED")

    def test_runway_not_freed_before_duration(self):
        make_runway(operating_mode="LANDING")
        plane = make_aircraft(callsign="FREE2", zone_status="QUEUE_LA", altitude=1000)
        self.runway_controller.assign_runway(plane, self.now)
        plane.refresh_from_db()
        freed = self.runway_controller.free_runway(plane, self.now + timedelta(seconds=20))
        self.assertFalse(freed)

    def test_runway_freed_after_takeoff_duration(self):
        make_runway(operating_mode="TAKEOFF")
        plane = make_aircraft(
            callsign="FREE3",
            zone_status="QUEUE_TO",
            scheduled_departure=self.now,
        )
        self.runway_controller.assign_runway(plane, self.now)
        plane.refresh_from_db()
        freed = self.runway_controller.free_runway(plane, self.now + timedelta(seconds=45))
        self.assertTrue(freed)
        plane.refresh_from_db()
        self.assertEqual(plane.zone_status, "DEPARTED")


class RunwayOptimisationTests(TestCase):

    def setUp(self):
        self.now = timezone.now()
        self.runway_controller = make_runway_controller()

    def test_mixed_runway_optimised_for_landing_when_emergency(self):
        make_runway(operating_mode="MIXED")
        make_aircraft(
            callsign="EMOPT1",
            zone_status="QUEUE_LA",
            emergency_status="MEDICAL",
            queue_entry_time=self.now,
            last_update=self.now,
            altitude=1000,
            fuel_mins=50,
        )
        self.runway_controller.optimise_runway_mode(self.now)
        runway = Runway.objects.first()
        self.assertEqual(runway.operating_mode, "LANDING")
        self.assertTrue(runway.temp_optimised)

    def test_mixed_runway_optimised_for_takeoff_when_cancellation_risk(self):
        make_runway(operating_mode="MIXED")
        risk_time = self.now - timedelta(minutes=30)
        make_aircraft(
            callsign="TOOPT1",
            zone_status="QUEUE_TO",
            queue_entry_time=risk_time,
            last_update=self.now,
        )
        self.runway_controller.optimise_runway_mode(self.now)
        runway = Runway.objects.first()
        self.assertEqual(runway.operating_mode, "TAKEOFF")

    def test_reset_optimised_runways(self):
        runway = make_runway(operating_mode="LANDING", )
        runway.temp_optimised = True
        runway.save()
        RunwayController.reset_optimised_runways()
        runway.refresh_from_db()
        self.assertEqual(runway.operating_mode, "MIXED")
        self.assertFalse(runway.temp_optimised)

    def test_occupied_runway_not_reset(self):
        occupant = make_aircraft(callsign="OCCR1", zone_status="RUNWAY_LA")
        runway = make_runway(operating_mode="LANDING")
        runway.temp_optimised = True
        runway.occupied_by = occupant
        runway.save()
        RunwayController.reset_optimised_runways()
        runway.refresh_from_db()
        # Should not be reset since it's occupied
        self.assertEqual(runway.operating_mode, "LANDING")


# ============================================================
# GENERATOR TESTS
# ============================================================

class GeneratorTests(TestCase):

    def setUp(self):
        self.now = timezone.now()
        RunStats.objects.create(id=1)

    def test_aircraft_generated_for_schedule_window(self):
        gen = Generator(
            hour_limit=2,
            inbound_per_hour=10,
            outbound_per_hour=10,
            start_time=self.now,
        )
        gen.run_generation(self.now)
        count = Aircraft.objects.filter(zone_status="SCHEDULED").count()
        self.assertGreater(count, 0)

    def test_inbound_aircraft_have_scheduled_arrival(self):
        gen = Generator(
            hour_limit=2,
            inbound_per_hour=10,
            outbound_per_hour=0,
            start_time=self.now,
        )
        gen.run_generation(self.now)
        aircraft = Aircraft.objects.filter(zone_status="SCHEDULED")
        for a in aircraft:
            self.assertIsNotNone(a.scheduled_arrival)
            self.assertIsNone(a.scheduled_departure)

    def test_outbound_aircraft_have_scheduled_departure(self):
        gen = Generator(
            hour_limit=2,
            inbound_per_hour=0,
            outbound_per_hour=10,
            start_time=self.now,
        )
        gen.run_generation(self.now)
        aircraft = Aircraft.objects.filter(zone_status="SCHEDULED")
        for a in aircraft:
            self.assertIsNotNone(a.scheduled_departure)
            self.assertIsNone(a.scheduled_arrival)

    def test_runway_generated_with_correct_mode(self):
        for mode in ["MIXED", "TAKEOFF", "LANDING"]:
            Generator.generate_runway(mode=mode)
        self.assertEqual(Runway.objects.filter(operating_mode="MIXED").count(), 1)
        self.assertEqual(Runway.objects.filter(operating_mode="TAKEOFF").count(), 1)
        self.assertEqual(Runway.objects.filter(operating_mode="LANDING").count(), 1)

    def test_no_aircraft_generated_when_zero_flow(self):
        gen = Generator(
            hour_limit=2,
            inbound_per_hour=0,
            outbound_per_hour=0,
            start_time=self.now,
        )
        gen.run_generation(self.now)
        self.assertEqual(Aircraft.objects.count(), 0)


# ============================================================
# RUNSTATS TESTS
# ============================================================

class RunStatsTests(TestCase):

    def setUp(self):
        self.stats = RunStats.objects.create(id=1)

    def test_add_stats_updates_sum_holding(self):
        self.stats.add_stats(10.0, 0)
        self.assertEqual(self.stats.sum_holding_time_mins, 10.0)

    def test_add_stats_updates_mean(self):
        self.stats.add_stats(10.0, 0)
        self.stats.add_stats(20.0, 0)
        self.assertAlmostEqual(self.stats.holding_mean, 15.0)

    def test_true_variance_correct(self):
        values = [10.0, 20.0, 30.0]
        for v in values:
            self.stats.add_stats(v, 0)
        expected_variance = 100.0  # sample variance of [10, 20, 30]
        self.assertAlmostEqual(self.stats.true_variance(0), expected_variance)

    def test_true_variance_returns_none_for_single_value(self):
        self.stats.add_stats(10.0, 0)
        self.assertIsNone(self.stats.true_variance(0))

    def test_max_tracking(self):
        self.stats.update_max_holding_pattern(5)
        self.stats.update_max_holding_pattern(10)
        self.stats.update_max_holding_pattern(3)
        self.stats.refresh_from_db()
        self.assertEqual(self.stats.max_num_holding_pattern, 10)

    def test_min_tracking(self):
        self.stats.update_min_holding_pattern(10)
        self.stats.update_min_holding_pattern(5)
        self.stats.update_min_holding_pattern(8)
        self.stats.refresh_from_db()
        self.assertEqual(self.stats.min_num_holding_pattern, 5)

    def test_arrival_delay_ignores_early_arrivals(self):
        # Negative delay (early arrival) should not be added to the sum
        self.stats.add_stats(-5.0, 2)
        self.assertEqual(self.stats.sum_arrival_delay_mins, 0.0)

    def test_departure_delay_ignores_early_departures(self):
        self.stats.add_stats(-10.0, 3)
        self.assertEqual(self.stats.sum_departure_delay_mins, 0.0)


# ============================================================
# INTEGRATION TESTS
# ============================================================

class SimulationIntegrationTests(TestCase):

    def setUp(self):
        self.now = timezone.now()
        make_config()
        self.controller = Controller(launch_time=self.now)
        self.controller.setup_simulation()

    def test_aircraft_progress_through_lifecycle(self):
        for _ in range(50):  # was 20
            self.controller.run_simulation()
        active = Aircraft.objects.exclude(zone_status="SCHEDULED").count()
        self.assertGreater(active, 0)

    def test_aircraft_land_and_depart(self):
        for _ in range(20):
            self.controller.run_simulation()
        completed = Aircraft.objects.filter(
            zone_status__in=["LANDED", "DEPARTED"]
        ).count()
        self.assertGreater(completed, 0)

    def test_stats_recorded_after_ticks(self):
        for _ in range(20):
            self.controller.run_simulation()
        stats = RunStats.objects.first()
        self.assertIsNotNone(stats)
        self.assertGreaterEqual(stats.max_num_holding_pattern, 0)
        self.assertGreaterEqual(stats.max_num_takeoff_queue, 0)

    def test_no_runway_double_occupancy(self):
        for _ in range(20):
            self.controller.run_simulation()
        for runway in Runway.objects.all():
            count = Aircraft.objects.filter(
                assigned_runway=runway,
                zone_status__in=["RUNWAY_LA", "RUNWAY_TO"]
            ).count()
            self.assertLessEqual(count, 1)

    def test_emergency_aircraft_prioritised(self):
        normal = make_aircraft(
            callsign="NORM1",
            zone_status="QUEUE_LA",
            emergency_status="NONE",
            queue_entry_time=self.now,
            altitude=2000,
            fuel_mins=50,
            last_update=self.now,
        )
        emergency = make_aircraft(
            callsign="EMRG1",
            zone_status="QUEUE_LA",
            emergency_status="MEDICAL",
            queue_entry_time=self.now + timedelta(seconds=10),
            altitude=1000,
            fuel_mins=50,
            last_update=self.now,
        )
        for _ in range(10):
            self.controller.run_simulation()
        emergency.refresh_from_db()
        normal.refresh_from_db()
        emergency_done = emergency.zone_status in ["RUNWAY_LA", "LANDED"]
        normal_still_waiting = normal.zone_status in ["QUEUE_LA", "RUNWAY_LA"]
        self.assertTrue(emergency_done or normal_still_waiting)

    def test_diversions_occur_under_low_fuel(self):
        make_aircraft(
            callsign="DIVINT1",
            zone_status="QUEUE_LA",
            fuel_mins=5,
            altitude=1000,
            last_update=self.now - timedelta(minutes=10),
        )
        for _ in range(5):
            self.controller.run_simulation()
        diverted = Aircraft.objects.filter(zone_status="DIVERTED").count()
        self.assertGreater(diverted, 0)

    def test_cancellations_occur_after_max_wait(self):
        make_aircraft(
            callsign="CANINT1",
            zone_status="QUEUE_TO",
            queue_entry_time=self.now - timedelta(minutes=120),
            scheduled_departure=self.now - timedelta(minutes=120),
            last_update=self.now,
        )
        for _ in range(5):
            self.controller.run_simulation()
        cancelled = Aircraft.objects.filter(zone_status="CANCELLED").count()
        self.assertGreater(cancelled, 0)

    def test_simulation_stops_when_stop_flag_set(self):
        config = RunConfig.objects.last()
        config.stop = True
        config.save()
        self.controller.update_configuration()  # pull the change in
        self.assertTrue(self.controller.check_simulation_end())