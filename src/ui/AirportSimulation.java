package ui;

import logic.Controller;
import javax.swing.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

public class AirportSimulation extends JFrame {
    private Controller controller;
    private Timer simulationTimer;

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
