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
    
    altitude = models.FloatField(default=0.0)
    fuel_mins = models.FloatField(default=0.0)   # Renamed for clarity
    
    # Status flags
    emergency_status = models.BooleanField(default=False)
    
    # Zone Status
    ZONE_CHOICES = [
        ('LANDED', 'Landed'),
        ('RUNWAY_LA', 'On runway for landing'),
        ('RUNWAY_TO', 'On runway for takeoff'),
        ('QUEUE_LA', 'Queue to land (holding pattern)'),
        ('QUEUE_TO', 'Queue to takeoff'),
        ('DEPARTED', 'Departed'),
    ]
    zone_status = models.CharField(max_length=20, choices=ZONE_CHOICES)

    def __str__(self):
        return f"{self.callsign} ({self.zone_status})"


class Runway(models.Model):
    # Django automatically creates 'id' for runwayID
    
    runway_number = models.CharField(max_length=10) 
    length = models.IntegerField(help_text="Length in meters")
    bearing = models.IntegerField(help_text="Heading in degrees")
    
    # Mode: e.g., "Takeoff Only", "Landing Only", "Mixed"
    operating_mode = models.CharField(max_length=20, default="Mixed")
    
    # Operational Status: "Available", "Runway Inspection", "Snow Clearance", "Equipment Failure"
    operational_status = models.CharField(max_length=20, default="Available")

    def __str__(self):
        status = "OPEN" if self.operational_status == "Available" else "CLOSED"
        return f"Runway {self.runway_number} ({status})"