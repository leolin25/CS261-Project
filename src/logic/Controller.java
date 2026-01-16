package logic;

import objects.Aircraft;
import objects.Runway;
import java.util.ArrayList;

public class Controller {
    public ArrayList<Aircraft> holdPattern = new ArrayList<>();
    public ArrayList<Aircraft> takeoffQueue = new ArrayList<>();
    public ArrayList<Runway> runways = new ArrayList<>();

    // Create lists to store data for stats table (+ve for delay, -ve for early)
    public ArrayList<Integer> takeoffVariation = new ArrayList<>();
    public ArrayList<Integer> arrivalVariation = new ArrayList<>();
    public ArrayList<Integer> takeoffQueueWait = new ArrayList<>();
    public ArrayList<Integer> holdingQueueWait = new ArrayList<>();

    // A tick has been processed, move a minute into simulation
    public void tick() {
        // Every second, this will reduce fuel and check for arrivals
    }

    // Takeoff time data (minutes)
    public double getTakeoffVariance() {
        return 0.0;
    }

    public double getAverageTakeoff() {
        return 0.0;
    }

    public double getRangeTakeoff() {
        return 0.0;
    }

    public double getUpperQuartileTakeoff() {
        return 0.0;
    }

    public double getLowerQuartileTakeoff() {
        return 0.0;
    }

    public double getMaxTakeoff() {
        return 0.0;
    }

    // Arrival time data (minutes)
    public double getArrivalVariance() {
        return 0.0;
    }

    public double getAverageArrival() {
        return 0.0;
    }

    public double getRangeArrival() {
        return 0.0;
    }

    public double getUpperQuartileArrival() {
        return 0.0;
    }

    public double getLowerQuartileArrival() {
        return 0.0;
    }

    public double getMaxArrival() {
        return 0.0;
    }

    // Holding queue time data (minutes)
    public double getAverageHoldingQueueTime() {
        return 0.0;
    }

    public double getVarianceHoldingQueueTime() {
        return 0.0;
    }

    public double getRangeHoldingQueueTime() {
        return 0.0;
    }

    public double getLowerQuartileHoldingQueueTime() {
        return 0.0;
    }

    public double getUpperQuartileHoldingQueueTime() {
        return 0.0;
    }

    public double getMaxHoldingQueueTime() {
        return 0.0;
    }

    // Takeoff queue time data (minutes)
    public double getAverageTakeoffQueueTime() {
        return 0.0;
    }

    public double getVarianceTakeoffQueueTime() {
        return 0.0;
    }

    public double getRangeTakeoffQueueTime() {
        return 0.0;
    }

    public double getLowerQuartileTakeoffQueueTime() {
        return 0.0;
    }

    public double getUpperQuartileTakeoffQueueTime() {
        return 0.0;
    }

    public double getMaxTakeoffQueueTime() {
        return 0.0;
    }
}