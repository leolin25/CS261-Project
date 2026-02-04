from django.db import models

class Aircraft(models.Model):
    # Note: Django automatically creates an 'id' field for aircraftID
    
    callsign = models.CharField(max_length=20, unique=True)
    operator = models.CharField(max_length=100)  
    origin = models.CharField(max_length=4)
    destination = models.CharField(max_length=4) 
    
    # Times can be empty (null=True) depending on if it's Arrival vs Departure
    scheduled_arrival = models.DateTimeField(null=True, blank=True)
    scheduled_departure = models.DateTimeField(null=True, blank=True)

    # Record when the aircraft has entered the queue for landing or takeoff
    queue_entry_time = models.DateTimeField(null=True, blank=True)
    
    altitude = models.IntegerField(default=0)
    fuel_mins = models.IntegerField(default=0)

    # Emergency Status
    EMERGENCY_CHOICES = [
        ('NONE', 'None'),
        ('FUEL', 'Low Fuel'),
        ('MECHANICAL', 'Mechanical Failure'),
        ('MEDICAL', 'Passenger Health'),
    ]
    # Default is now the string 'NONE' instead of False
    emergency_status = models.CharField(
        max_length=20, 
        choices=EMERGENCY_CHOICES, 
        default='NONE'
    )
    
    # Zone Status
    ZONE_CHOICES = [
        ('SCHEDULED', 'In schedule (Hidden)'),
        ('LANDED', 'Landed'),
        ('RUNWAY_LA', 'On runway for landing'),
        ('RUNWAY_TO', 'On runway for takeoff'),
        ('QUEUE_LA', 'Queue to land (holding pattern)'),
        ('QUEUE_TO', 'Queue to takeoff'),
        ('DEPARTED', 'Departed'),
        ('CANCELLED', 'Cancelled'),
        ('DIVERTED', 'Diverted'),
    ]
    zone_status = models.CharField(max_length=20, choices=ZONE_CHOICES)

    def __str__(self):
        return f"{self.callsign} ({self.zone_status})"


class Runway(models.Model):
    # Django automatically creates 'id' for runwayID
    
    runway_number = models.CharField(max_length=20, unique=True)
    length = models.IntegerField(help_text="Length in meters")
    bearing = models.IntegerField(help_text="Heading in degrees")
    
    # Mode: e.g., "Takeoff Only", "Landing Only", "Mixed"
    operating_mode = models.CharField(max_length=20, default="Mixed")
    
    # Operational Status: "Available", "Runway Inspection", "Snow Clearance", "Equipment Failure"
    OPERATIONAL_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('RUNWAYINSPEC', 'Runway Inspection'),
        ('SNOWCLEAR', 'Snow Clearance'),
        ('EQUIPFAIL', 'Equipment Failure'),
    ]
    operational_status = models.CharField(max_length=20, choices=OPERATIONAL_CHOICES)

    def __str__(self):
        status = "OPEN" if self.operational_status == "Available" else "CLOSED"
        return f"Runway {self.runway_number} ({status})"
    
class FlightStats(models.Model):
    # Django automatically creates 'id' for statsID

    callsign = models.CharField(max_length=20)
    
    # The 4 Key Stats
    holding_time_mins = models.FloatField(default=0.0)
    takeoff_queue_time_mins = models.FloatField(default=0.0)
    arrival_delay_mins = models.FloatField(default=0.0)
    departure_delay_mins = models.FloatField(default=0.0)

    # What happened to the flight (Landed, Departed, Cancelled, Diversion)
    OUTCOME = [
        ('LANDED', 'Landed'),
        ('DEPARTED', 'Departed'),
        ('CANCELLED', 'Cancelled'),
        ('DIVERTED', 'Diverted'),
    ]
    outcome = models.CharField(max_length=20, choices=OUTCOME, default='LANDED')

    time_recorded = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Stats for {self.callsign}"