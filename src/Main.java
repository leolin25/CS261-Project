import objects.Aircraft;
import objects.Runway;
import logic.Controller;
import ui.AirportSimulation;

public class Main {
    public static void main(String[] args) {
        Controller controller = new Controller();

        // Create a connection between ui and controller
        javax.swing.SwingUtilities.invokeLater(() -> {
            AirportSimulation simulation = new AirportSimulation(controller);
            simulation.setVisible(true);
        });

        System.out.println("Airport Simulation Initialized.");
    }
}