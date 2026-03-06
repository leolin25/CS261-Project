from django.db import models


class Aircraft(models.Model):
    # Note: Django automatically creates an 'id' field for aircraftID
    callsign = models.CharField(max_length=20)
    operator = models.CharField(max_length=100)  
    origin = models.CharField(max_length=4)
    destination = models.CharField(max_length=4) 
    
    # Times can be empty (null=True) depending on if it's Arrival vs Departure
    scheduled_arrival = models.DateTimeField(null=True, blank=True)
    scheduled_departure = models.DateTimeField(null=True, blank=True)

    # Record when the aircraft has entered the queue for landing or takeoff
    queue_entry_time = models.DateTimeField(null=True, blank=True)

    # Record the runway this plane has been assigned
    assigned_runway = models.ForeignKey(
        'Runway',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
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

    last_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.callsign} ({self.zone_status})"


class Runway(models.Model):
    # Django automatically creates 'id' for runwayID
    length = models.IntegerField(help_text="Length in meters")
    bearing = models.IntegerField(help_text="Heading in degrees")
    
    # Mode: e.g., "Takeoff Only", "Landing Only", "Mixed"
    MODE_CHOICES = [
        ('LANDING', 'Landing'),
        ('TAKEOFF', 'Takeoff'),
        ('MIXED', 'Mixed'),
    ]
    operating_mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    
    # Operational Status: "Available", "Runway Inspection", "Snow Clearance", "Equipment Failure"
    OPERATIONAL_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('RUNWAYINSPEC', 'Runway Inspection'),
        ('SNOWCLEAR', 'Snow Clearance'),
        ('EQUIPFAIL', 'Equipment Failure'),
        ('OCCUPIED', 'Occupied'),
    ]
    # Updated so runway now also tracks which aircraft is on it 
    occupied_by = models.ForeignKey(
        'Aircraft', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='current_runway'
    )
    # Updated so runway tracks when the aircraft started using the runway.
    time_occupied = models.DateTimeField(null=True, blank=True)

    operational_status = models.CharField(max_length=20, choices=OPERATIONAL_CHOICES)

    temp_optimised = models.BooleanField(default=False)

    def __str__(self):
        status = "OPEN" if self.operational_status == "Available" else "CLOSED"
        return f"Runway {self.bearing} ({status})"


class RunStats(models.Model):
    
    # A summation of all plane stats
    holding_time_mins = models.FloatField(default=0.0)             # time spent in holding pattern
    takeoff_queue_time_mins = models.FloatField(default=0.0)       # waiting time in takeoff queue
    arrival_delay_mins = models.FloatField(default=0.0)            # delay in arrival time
    departure_delay_mins = models.FloatField(default=0.0)          # delay in departure time

    # Variance of the above stats
    holding_time_variance = models.FloatField(default=0.0) 
    holding_num = 0 # Count the total number of planes, used in calculating variance
    holding_mean = 0
    takeoff_queue_time_variance = models.FloatField(default=0.0) 
    takeoff_num = 0 
    takeoff_mean = 0
    arrival_delay_variance = models.FloatField(default=0.0) 
    arrival_num = 0 
    arrival_mean = 0
    departure_delay_variance = models.FloatField(default=0.0) 
    departure_num = 0 
    departure_mean = 0
                                                                
    max_num_takeoff_queue = 0         # max number of planes held in the takeoff queue
    max_num_holding_pattern = 0       # max number of planes held in holding pattern
    max_arrival_delay_mins = 0        # maximum arrival delay time
    max_departure_delay = 0           # maximum departure delay time
    max_num_cancelled = 0             # maximum number of planes cancelled
    max_num_diverted = 0              # maximum number of planes diverted
    
    min_num_takeoff_queue = 0         # min number of planes held in the takeoff queue
    min_num_holding_pattern = 0       # min number of planes held in holding pattern
    min_arrival_delay_mins = 0        # minimum arrival delay time
    min_departure_delay = 0           # minimum departure delay time
    min_num_cancelled = 0             # minimum number of planes cancelled
    min_num_diverted = 0              # minimum number of planes diverted
    
    
    # Adds the new stats to the sum of stats
    # Updates the variance and mean at the same time
    # The meaning of the value held by "new_num" is determined by "indicator"
    # The second parameter "indicator", can be set between 0-3 corresponding to 
    # holding time, takeoff queue time, arrival delay, departure delay.
    @staticmethod
    def add_stats(new_num, indicator):
        delta = 0
        
        # Indicator = 0 means input parameter stores holding time value
        if indicator == 0:
            RunStats.holding_time_mins += new_num 
            RunStats.holding_num += 1
            delta = (new_num - RunStats.holding_mean)
            RunStats.holding_mean += delta / RunStats.holding_num
            RunStats.holding_time_variance += (new_num - RunStats.holding_mean) * delta
        
        # Indicator = 1 means input parameter stores takeoff queue wait time value
        elif indicator == 1:
            RunStats.takeoff_queue_time_mins += new_num
            RunStats.takeoff_num += 1
            delta = (new_num - RunStats.takeoff_mean)
            RunStats.takeoff_mean += delta / RunStats.takeoff_num
            RunStats.takeoff_queue_time_variance += (new_num - RunStats.takeoff_mean) * delta
        
        # Indicator = 2 means input parameter stores arrival delay value
        elif indicator == 2:
            RunStats.arrival_delay_mins += new_num
            RunStats.arrival_num += 1
            delta = (new_num - RunStats.arrival_mean)
            RunStats.arrival_mean += delta / RunStats.arrival_num
            RunStats.arrival_delay_variance += (new_num - RunStats.arrival_mean) * delta
        
        # Indicator = 3 means input parameter stores departure delay value
        elif indicator == 3:
            RunStats.departure_delay_mins += new_num
            RunStats.departure_num += 1
            delta = (new_num - RunStats.departure_mean)
            RunStats.departure_mean += delta / RunStats.departure_num
            RunStats.departure_delay_variance += (new_num - RunStats.departure_mean) * delta

    # Update maximum values ------------------------------------------

    # Updates the maximum number of planes in the takeoff queue
    @staticmethod
    def update_max_takeoff_queue(new_num):
        if new_num > RunStats.max_num_takeoff_queue:
            RunStats.max_num_takeoff_queue = new_num
    
    # Updates the maximum number of planes in the holding pattern
    @staticmethod
    def update_max_holding_pattern(new_num):
        if new_num > RunStats.max_num_holding_pattern:
            RunStats.max_num_holding_pattern = new_num
    
    # Updates the maximum arrival delay
    @staticmethod
    def update_max_arrival_delay(new_num):
        if new_num > RunStats.max_arrival_delay_mins:
            RunStats.max_arrival_delay_mins = new_num
    
    # Updates the maximum departure delay
    @staticmethod
    def update_max_departure_delay(new_num):
        if new_num > RunStats.max_departure_delay:
            RunStats.max_departure_delay = new_num
    
    # Updates the maximum planes cancelled
    @staticmethod
    def update_max_cancelled(new_num):
        if new_num > RunStats.max_num_cancelled:
            RunStats.max_num_cancelled = new_num
    
    # Updates the maximum planes diverted
    @staticmethod
    def update_max_diverted(new_num):
        if new_num > RunStats.max_num_diverted:
            RunStats.max_num_diverted = new_num
    
    
    # Update minimum values ------------------------------------------
    
    # Updates the minimum number of planes in the takeoff queue
    @staticmethod
    def update_max_takeoff_queue(new_num):
        if new_num < RunStats.min_num_takeoff_queue:
            RunStats.min_num_takeoff_queue = new_num
    
    # Updates the minimum number of planes in the holding pattern
    @staticmethod
    def update_min_holding_pattern(new_num):
        if new_num < RunStats.min_num_holding_pattern:
            RunStats.min_num_holding_pattern = new_num
    
    # Updates the minimum arrival delay
    @staticmethod
    def update_min_arrival_delay(new_num):
        if new_num < RunStats.min_arrival_delay_mins:
            RunStats.min_arrival_delay_mins = new_num
    
    # Updates the minimum departure delay
    @staticmethod
    def update_min_departure_delay(new_num):
        if new_num < RunStats.min_departure_delay:
            RunStats.min_departure_delay = new_num
    
    # Updates the minimum planes cancelled
    @staticmethod
    def update_min_cancelled(new_num):
        if new_num < RunStats.min_num_cancelled:
            RunStats.min_num_cancelled = new_num
    
    # Updates the minimum planes diverted
    @staticmethod
    def update_min_diverted(new_num):
        if new_num < RunStats.min_num_diverted:
            RunStats.min_num_diverted = new_num
        
    