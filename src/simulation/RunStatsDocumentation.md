# RunStats Class Documentation

## Data Tracking Categories

The model is broken down into four primary categories of fields:

1. **Cumulative Sums (`sum_*`):** Tracks the total accumulated minutes for various metrics (e.g., total holding time for all planes combined).
2. **Trackers (`*_variance`, `*_mean`):** Groups of variables which store the calculated variance and mean.
3. **Maximum Extremes (`max_*`):** Stores max of a variable that has been seen during the simulation
4. **Minimum Extremes (`min_*`):** Stores min of a variable that has been seen during the simulation
5. **Number of Samples (`*_num`)** Stores the amount of samples we have of arrival and departing planes

---

## Methods

### `add_stats(self, new_num, indicator)`
The primary method for logging new time/delay data points into the simulation's statistics. It automatically adds to the cumulative sum, increments the plane counter, and updates the rolling mean and variance.

**Parameters:**
* `new_num` *(float)*: The value of the stat being recorded (e.g., a plane waited 15.5 minutes).
* `indicator` *(int)*: A routing number that determines which stat category to update:
  * `0`: Holding pattern time
  * `1`: Takeoff queue wait time
  * `2`: Arrival delay
  * `3`: Departure delay

> **Note on Variance:** The `*_variance` fields store the *Sum of Squared Differences (SSD)*. To get the true mathematical sample variance at the end of the simulation, you must divide this field by `(num - 1)`. This converts the SSD to a true variance.

### `update_max_*(self, new_num)`
A group of functions that takes a new value, compares it against the current highest recorded value in the database, and overwrites it if the new value is larger.
* `update_max_takeoff_queue(new_num)`
* `update_max_holding_pattern(new_num)`
* `update_max_arrival_delay(new_num)`
* `update_max_departure_delay(new_num)`
* `update_max_cancelled(new_num)`
* `update_max_diverted(new_num)`

### `update_min_*(self, new_num)`
A group of functions that tracks the lowest recorded values. These include a fail-safe (`== 0`) so that the very first recorded plane successfully overwrites the default `0` starting value, preventing the minimums from being permanently locked at zero.
* `update_min_takeoff_queue(new_num)`
* `update_min_holding_pattern(new_num)`
* `update_min_arrival_delay(new_num)`
* `update_min_departure_delay(new_num)`
* `update_min_cancelled(new_num)`
* `update_min_diverted(new_num)`

### `true_variance(self, indicator)`
A function that takes an indicator and returns the variance of a set of data depending on the indicator. Refer to indicator table if you want to see what data to refer to.

---

## Saving Behavior & Usage

Every method inside `RunStats` automatically ends with `self.save()`. This ensures that whenever a function is called, the updated numbers are instantly permanently written to the Django database.

This means there is no reason to call `.save()` since it is already handled by the method and would cause unnecessary lag.

### Example Usage:
```python

# Remember to include RunStats in the imports from .models
from .models import RunStats

# Grab the current simulation stats row
stats = RunStats.objects.first()

if stats:
    # Log that a plane waited 12 minutes in the takeoff queue
    stats.add_stats(12.0, indicator=1)
    
    # Check if 5 planes is a new maximum for the holding pattern
    stats.update_max_holding_pattern(5)