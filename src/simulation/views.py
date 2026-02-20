from datetime import timedelta
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template import loader
from django.utils import timezone
from django.db.models import Avg, Max, Min

from .models import Aircraft, Runway, FlightStats
from .logic import generate_random_aircraft
from .RunwayController import RunwayController
from .departure_logic import DepartureManager


# --- Helpers -------------------------------------------------------------

MODE_MAP = {
    "landing": "LANDING",
    "takeoff": "TAKEOFF",
    "mixed": "MIXED",
}

STATUS_MAP = {
    "available": "AVAILABLE",
    "inspection": "RUNWAYINSPEC",
    "snow": "SNOWCLEAR",
    "equipment_failure": "EQUIPFAIL",
}


def _reset_simulation_data():
    """
    Optional but recommended: clears prior runs so results aren't polluted.
    """
    FlightStats.objects.all().delete()
    Aircraft.objects.all().delete()
    Runway.objects.all().delete()
    DepartureManager.max_queue_size = 0


def _create_runways(num_runways: int, mode: str, status: str):
    """
    Creates N runways with unique runway_number, random bearing/length,
    but configured to the chosen mode/status.
    """
    import random

    existing_numbers = set(Runway.objects.values_list("runway_number", flat=True))

    for _ in range(num_runways):
        bearing = random.randint(0, 359)
        length = random.randint(2000, 4000)

        # runway number derived from bearing, ensure unique
        runway_number = f"{round(bearing / 10):02d}"
        attempts = 0
        while runway_number in existing_numbers and attempts < 50:
            bearing = (bearing + 10) % 360
            runway_number = f"{round(bearing / 10):02d}"
            attempts += 1

        existing_numbers.add(runway_number)

        Runway.objects.create(
            runway_number=runway_number,
            length=length,
            bearing=bearing,
            operating_mode=mode,
            operational_status=status,
        )


def _schedule_departure_aircraft(outbound_per_hour: int, start_time):
    """
    Creates outbound_per_hour scheduled departures across the next hour.
    """
    if outbound_per_hour <= 0:
        return

    step_minutes = 60 / outbound_per_hour
    for i in range(outbound_per_hour):
        sched = start_time + timedelta(minutes=i * step_minutes)
        # DepartureManager will add queue_entry_time variance later
        generate_random_aircraft(is_arrival=False, scheduled_time=sched)


def _schedule_arrival_aircraft(inbound_per_hour: int, start_time):
    """
    Arrival logic in your archive is empty, but we can at least create inbound flights
    and put them into the landing queue so they show on the simulation page.
    """
    if inbound_per_hour <= 0:
        return

    step_minutes = 60 / inbound_per_hour
    for i in range(inbound_per_hour):
        sched = start_time + timedelta(minutes=i * step_minutes)
        # create scheduled arrival
        generate_random_aircraft(is_arrival=True, scheduled_time=sched, queue_entry_time=sched)
        # put latest created ARRIVAL aircraft into QUEUE_LA (best-effort)
        # (generate_random_aircraft doesn’t return the object, so we update the newest scheduled arrival)
        latest = Aircraft.objects.filter(scheduled_arrival=sched).order_by("-id").first()
        if latest:
            latest.zone_status = "QUEUE_LA"
            latest.queue_entry_time = sched
            latest.save()


def _compute_delay_variance_python(values):
    """
    Fallback variance (population variance) computed in Python.
    """
    if not values:
        return None
    n = len(values)
    mean = sum(values) / n
    return sum((x - mean) ** 2 for x in values) / n


# --- Views ---------------------------------------------------------------

def home(request):
    return render(request, "pages/home.html")


def simulation(request):
    """
    Shows live queues from the DB.
    """
    takeoff_queue = Aircraft.objects.filter(zone_status="QUEUE_TO").order_by("queue_entry_time")
    landing_queue = Aircraft.objects.filter(zone_status="QUEUE_LA").order_by("queue_entry_time")

    return render(
        request,
        "pages/simulationtables.html",
        {
            "takeoff_queue": takeoff_queue,
            "landing_queue": landing_queue,
        },
    )


def results(request):
    """
    Handles POST from home.html, runs a 1-hour simulation loop (1-min steps),
    then renders results.html with real numbers.
    """
    if request.method != "POST":
        return redirect("home")

    inbound_flow = int(request.POST.get("inbound_flow", 0))
    outbound_flow = int(request.POST.get("outbound_flow", 0))
    num_runways = int(request.POST.get("num_runways", 1))
    runway_mode_ui = request.POST.get("runway_mode", "mixed")
    runway_status_ui = request.POST.get("runway_status", "available")
    random_events = True if request.POST.get("random_events") == "on" else False

    # Map UI → model values
    runway_mode = MODE_MAP.get(runway_mode_ui, "MIXED")
    runway_status = STATUS_MAP.get(runway_status_ui, "AVAILABLE")

    # Start fresh each time
    _reset_simulation_data()

    # Create runways + aircraft
    _create_runways(num_runways=num_runways, mode=runway_mode, status=runway_status)

    start = timezone.now()
    _schedule_departure_aircraft(outbound_flow, start)
    _schedule_arrival_aircraft(inbound_flow, start)

    # Run the departure sim for 1 hour in 1-minute ticks
    runway_controller = RunwayController()

    end = start + timedelta(hours=1)
    t = start
    while t <= end:
        DepartureManager.process_departures(t, runway_controller)
        t += timedelta(minutes=1)

    # Departure stats (from FlightStats)
    departed_stats = FlightStats.objects.filter(outcome="DEPARTED")
    agg = departed_stats.aggregate(
        max_delay=Max("departure_delay_mins"),
        avg_delay=Avg("departure_delay_mins"),
        min_delay=Min("departure_delay_mins"),
    )

    # delay range
    if agg["max_delay"] is not None and agg["min_delay"] is not None:
        delay_range = agg["max_delay"] - agg["min_delay"]
    else:
        delay_range = None

    # variance: sqlite + django variance aggregation is unreliable, do python variance
    delays = list(departed_stats.values_list("departure_delay_mins", flat=True))
    delay_variance = _compute_delay_variance_python(delays)

    # Landing stats placeholders (arrival_logic.py is empty in your archive)
    # We still show max landing queue size observed *at end* (you can improve later)
    max_in_landing_q = Aircraft.objects.filter(zone_status="QUEUE_LA").count()

    template = loader.get_template("pages/results.html")
    context = {
        # config
        "inperhour": inbound_flow,
        "outperhour": outbound_flow,
        "numrunways": num_runways,
        "mixedorsingle": runway_mode.upper(),
        "randomevents": "ON" if random_events else "OFF",

        # statistics (real for departures, placeholders for arrivals until arrival_logic is implemented)
        "maxintakeoffQ": DepartureManager.max_queue_size,
        "maxinlandingQ": max_in_landing_q,
        "maxinholding": 0,
        "averagehold": 0,

        "maxdelay": agg["max_delay"] if agg["max_delay"] is not None else 0,
        "averagedelay": round(agg["avg_delay"], 2) if agg["avg_delay"] is not None else 0,

        # advanced
        "delayvariance": round(delay_variance, 2) if delay_variance is not None else 0,
        "delayrange": round(delay_range, 2) if delay_range is not None else 0,
        "numdiverted": 0,
    }
    return HttpResponse(template.render(context, request))