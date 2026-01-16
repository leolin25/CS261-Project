package objects;

public class Runway {
    public int runwayNumber;
    public String mode; // Landing, Take-off, or Mixed
    public boolean isAvailable;

    public Runway(int runwayNumber) {
        this.runwayNumber = runwayNumber;
        this.isAvailable = true;
    }

    public String getMode() {
        return mode;
    }

    public boolean isAvailable() {
        return isAvailable;
    }
}