package objects;

import java.util.Random;

public class Aircraft {
    public String callsign;
    public String operator;
    public int fuel; // 20-60 range
    public boolean isEmergency;

    public Aircraft(String callsign, String operator) {

        // This will eventually randomize fuel and set initial altitude
    }

    // Get amount of fuel as minutes
    public int getFuel() {
        return fuel;
    }

    // Check if there is an emergency
    public boolean isEmergency() {
        return isEmergency;
    }
}