package objects;

public class Runway {
    public int id;
    public String mode; // Landing, Take-off, or Mixed
    public boolean isAvailable; // False if Snow Clearance in progress

    public Runway(int id) {
        this.id = id;
        this.isAvailable = true;
    }
}