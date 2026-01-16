package ui;

import logic.Controller;
import javax.swing.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

public class AirportSimulation extends JFrame {
    private Controller controller;
    private Timer simulationTimer;

    /**
     * User input:
     * - Amount of runways (cap amount of runways at 10)
     * - Inbound flow per hour
     * - Outbound flow per hour
     *
     * Create dropdowns for each runway to change mode from mixed, takeoff or landing
     * Runway should have another drop down to specify if it is operational or not
     *
     * UI should be able to display stats from Controller class
     *
     * UI should be able to show all aircraft in holding queue and takeoff queue
     * */

    // Constructor method except controller
    public AirportSimulation(Controller controller) {
        this.controller = controller;
        this.setTitle("Airport Management System");
        this.setSize(800, 600); // I haven't checked these values (change these)
        this.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);

        // Every second we move a tick and call the controller
        simulationTimer = new Timer(1000, new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                runSimulationTick();
            }
        });

        simulationTimer.start();
    }

    // This method should run every second (real time) and represent a single minute in the simulation
    private void runSimulationTick() {
        // Controller processes the math for a single tick (planes lose 1 min fuel, new averages and variances etc)
        controller.tick();

        // TODO: Update UI elements after the logic tick update has been done
    }
}
