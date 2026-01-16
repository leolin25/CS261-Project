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

    public double getAverageWaitTime() {
        return 0.0;
    }
}