import objects.Aircraft;
import objects.Runway;
import logic.Controller;
import ui.AirportSimulation;

public class Main {
    public static void main(String[] args) {
        Controller controller = new Controller();
        AirportSimulation gui = new AirportSimulation(controller);
        gui.setVisible(true);
    }
}