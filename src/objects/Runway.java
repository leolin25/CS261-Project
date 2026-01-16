package objects;

public class Runway {
    public int runwayNumber;
    public String mode; // Landing, Take-off, or Mixed
    public boolean isAvailable;

    public Runway(int runwayNumber) {
        this.runwayNumber = runwayNumber;
        this.isAvailable = true;
    }

    // Getter method for mode, mode can be landing, take-off or mixed
    public String getMode() {
        return mode;
    }

    // Method which returns whether the runway is available
    public boolean isAvailable() {
        return isAvailable;
    }
}