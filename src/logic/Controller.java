package logic;

import objects.Aircraft;
import objects.Runway;
import java.util.ArrayList;

public class Controller {
    public ArrayList<Aircraft> landings = new ArrayList<>();
    public ArrayList<Runway> runways = new ArrayList<>();

    public void tick() {
        // Every second, this will reduce fuel and check for arrivals
    }

    public double getAverageWaitTime() {
        return 0.0;
    }
}