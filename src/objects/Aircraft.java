package objects;

public class Aircraft {
    public String callsign;
    public String operator;
    public int fuel; // 20-60 range
    public int altitude; // 2500ft steps
    public boolean isEmergency;

    public Aircraft(String callsign, String operator) {
        // This will eventually randomize fuel and set initial altitude
    }
}