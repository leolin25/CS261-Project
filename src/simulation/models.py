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

    last_update = models.DateTimeField()
    final_state_time = models.DateTimeField(null=True, blank=True)

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


class RunConfig(models.Model):
    runways = models.IntegerField()
    runways_mixed = models.IntegerField()
    runways_takeoff = models.IntegerField()
    runways_landing = models.IntegerField()
    inbound_per_hour = models.IntegerField()
    outbound_per_hour = models.IntegerField()
    timescale = models.FloatField(default=1.0)
    schedule_limit = models.IntegerField(default=2)
    max_wait = models.IntegerField()
    landing_duration = models.IntegerField(default=45)
    takeoff_duration = models.IntegerField(default=45)
    fuel_risk_threshold = models.IntegerField(default=20)
    takeoff_risk_threshold = models.IntegerField(default=10)
    fuel_emergency_threshold = models.IntegerField(default=15)
    random_events = models.BooleanField()
    stop = models.BooleanField(default=False)


class RunStats(models.Model):
    # A summation of all plane stats
    sum_holding_time_mins = models.FloatField(default=0.0)             # time spent in holding pattern
    sum_takeoff_queue_time_mins = models.FloatField(default=0.0)       # waiting time in takeoff queue
    sum_arrival_delay_mins = models.FloatField(default=0.0)            # delay in arrival time
    sum_departure_delay_mins = models.FloatField(default=0.0)          # delay in departure time

    # Variance of the above stats
    # The variances here aren't actually the true variance, the actual variance is calculated through (variance/num - 1)
    holding_time_variance = models.FloatField(default=0.0) 
    holding_num = models.IntegerField(default=0)
    holding_mean = models.FloatField(default=0.0)

    takeoff_queue_time_variance = models.FloatField(default=0.0) 
    takeoff_num = models.IntegerField(default=0)
    takeoff_mean = models.FloatField(default=0.0)

    arrival_delay_variance = models.FloatField(default=0.0) 
    arrival_num = models.IntegerField(default=0) 
    arrival_mean = models.FloatField(default=0.0)
    
    departure_delay_variance = models.FloatField(default=0.0) 
    departure_num = models.IntegerField(default=0) 
    departure_mean = models.FloatField(default=0.0)
                                                                
    max_num_takeoff_queue = models.IntegerField(default=0)         # max number of planes held in the takeoff queue
    max_num_holding_pattern = models.IntegerField(default=0)       # max number of planes held in holding pattern
    max_arrival_delay_mins = models.IntegerField(default=0)        # maximum arrival delay time
    max_departure_delay = models.IntegerField(default=0)           # maximum departure delay time
    max_num_cancelled = models.IntegerField(default=0)             # maximum number of planes cancelled
    max_num_diverted = models.IntegerField(default=0)              # maximum number of planes diverted
    
    min_num_takeoff_queue = models.IntegerField(default=0)         # min number of planes held in the takeoff queue
    min_num_holding_pattern = models.IntegerField(default=0)       # min number of planes held in holding pattern
    min_arrival_delay_mins = models.IntegerField(default=0)        # minimum arrival delay time
    min_departure_delay = models.IntegerField(default=0)           # minimum departure delay time
    min_num_cancelled = models.IntegerField(default=0)             # minimum number of planes cancelled
    min_num_diverted = models.IntegerField(default=0)              # minimum number of planes diverted
    
    
    # Adds the new stats to the sum of stats
    # Updates the variance and mean at the same time
    # The meaning of the value held by "new_num" is determined by "indicator"
    # The second parameter "indicator", can be set between 0-3 corresponding to 
    # holding time, takeoff queue time, arrival delay, departure delay.
    def add_stats(self, new_num, indicator):
        # Indicator = 0 means input parameter stores holding time value
        if indicator == 0:
            new_count = self.holding_num + 1
            new_sum = self.sum_holding_time_mins + new_num
            new_mean = new_sum / new_count
            alpha = (self.holding_num - 1) * self.holding_time_variance
            beta = (new_num - self.holding_mean) * (new_num - new_mean)
            self.holding_time_variance = ((alpha + beta) / self.holding_num) if self.holding_num > 0 else 0.0
            self.holding_num = new_count
            self.sum_holding_time_mins = new_sum
            self.holding_mean = new_mean
        
        # Indicator = 1 means input parameter stores takeoff queue wait time value
        elif indicator == 1:
            new_count = self.takeoff_num + 1
            new_sum = self.sum_takeoff_queue_time_mins + new_num
            new_mean = new_sum / new_count
            alpha = (self.takeoff_num - 1) * self.takeoff_queue_time_variance
            beta = (new_num - self.takeoff_mean) * (new_num - new_mean)
            self.takeoff_queue_time_variance = ((alpha + beta) / self.takeoff_num) if self.takeoff_num > 0 else 0.0
            self.takeoff_num = new_count
            self.sum_takeoff_queue_time_mins = new_sum
            self.takeoff_mean = new_mean
        
        # Indicator = 2 means input parameter stores arrival delay value
        elif indicator == 2:
            new_num = max(0, new_num) # only consider delay, not early arrivals
            new_count = self.arrival_num + 1
            new_sum = self.sum_arrival_delay_mins + new_num
            new_mean = new_sum / new_count
            alpha = (self.arrival_num - 1) * self.arrival_delay_variance
            beta = (new_num - self.arrival_mean) * (new_num - new_mean)
            self.arrival_delay_variance = ((alpha + beta) / self.arrival_num) if self.arrival_num > 0 else 0.0
            self.arrival_num = new_count
            self.sum_arrival_delay_mins = new_sum
            self.arrival_mean = new_mean
        
        # Indicator = 3 means input parameter stores departure delay value
        elif indicator == 3:
            new_num = max(0, new_num)
            new_count = self.departure_num + 1
            new_sum = self.sum_departure_delay_mins + new_num
            new_mean = new_sum / new_count
            alpha = (self.departure_num - 1) * self.departure_delay_variance
            beta = (new_num - self.departure_mean) * (new_num - new_mean)
            self.departure_delay_variance = ((alpha + beta) / self.departure_num) if self.departure_num > 0 else 0.0
            self.departure_num = new_count
            self.sum_departure_delay_mins = new_sum
            self.departure_mean = new_mean

        self.save()

    # Update maximum values ------------------------------------------

    # Updates the maximum number of planes in the takeoff queue
    def update_max_takeoff_queue(self, new_num):
        if new_num > self.max_num_takeoff_queue:
            self.max_num_takeoff_queue = new_num
            self.save()
    
    # Updates the maximum number of planes in the holding pattern
    def update_max_holding_pattern(self, new_num):
        if new_num > self.max_num_holding_pattern:
            self.max_num_holding_pattern = new_num
            self.save()
    
    # Updates the maximum arrival delay
    def update_max_arrival_delay(self, new_num):
        if new_num > self.max_arrival_delay_mins:
            self.max_arrival_delay_mins = new_num
            self.save()
    
    # Updates the maximum departure delay
    def update_max_departure_delay(self, new_num):
        if new_num > self.max_departure_delay:
            self.max_departure_delay = new_num
            self.save()
    
    # Updates the maximum planes cancelled
    def update_max_cancelled(self, new_num):
        if new_num > self.max_num_cancelled:
            self.max_num_cancelled = new_num
            self.save()
    
    # Updates the maximum planes diverted
    def update_max_diverted(self, new_num):
        if new_num > self.max_num_diverted:
            self.max_num_diverted = new_num
            self.save()
    
    
    # Update minimum values ------------------------------------------
    
    # Updates the minimum number of planes in the takeoff queue
    def update_min_takeoff_queue(self, new_num):
        if new_num < self.min_num_takeoff_queue or self.min_num_takeoff_queue == 0:
            self.min_num_takeoff_queue = new_num
            self.save()
    
    # Updates the minimum number of planes in the holding pattern
    def update_min_holding_pattern(self, new_num):
        if new_num < self.min_num_holding_pattern or self.min_num_holding_pattern == 0:
            self.min_num_holding_pattern = new_num
            self.save()

    # Updates the minimum arrival delay
    def update_min_arrival_delay(self, new_num):
        if new_num < self.min_arrival_delay_mins or self.min_arrival_delay_mins == 0:
            self.min_arrival_delay_mins = new_num
            self.save()

    # Updates the minimum departure delay
    def update_min_departure_delay(self, new_num):
        if new_num < self.min_departure_delay or self.min_departure_delay == 0:
            self.min_departure_delay = new_num
            self.save()

    # Updates the minimum planes cancelled
    def update_min_cancelled(self, new_num):
        if new_num < self.min_num_cancelled or self.min_num_cancelled == 0:
            self.min_num_cancelled = new_num
            self.save()

    # Updates the minimum planes diverted
    def update_min_diverted(self, new_num):
        if new_num < self.min_num_diverted or self.min_num_diverted == 0:
            self.min_num_diverted = new_num
            self.save()

    # Returns the true variance of the stat corresponding to the indicator value
    # Indicator 1: holding time, 2: takeoff queue time, 3: arrival delay, 4: departure delay
    def true_variance(self, indicator):
        if indicator == 0 and self.holding_num > 1:
            return self.holding_time_variance / (self.holding_num - 1)
        elif indicator == 1 and self.takeoff_num > 1:
            return self.takeoff_queue_time_variance / (self.takeoff_num - 1)
        elif indicator == 2 and self.arrival_num > 1:
            return self.arrival_delay_variance / (self.arrival_num - 1)
        elif indicator == 3 and self.departure_num > 1:
            return self.departure_delay_variance / (self.departure_num - 1)
        else:
            return None
        