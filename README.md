# CS261-Project

The initial plan:
- Try incorporate the first 3 bullet points of the priority checklist (takeoff and holding pattern stats)

This repository has 4 branches (main, logic, object and ui). 

- 'main' is the main branch and shouldn't be edited directly
- All the other branches are sub-branches of 'main' and so contain the same files, people should work on individual branches and commit the changes to the 'main' branch after testing. Each branch corresponds to a package that should be updated.

Whoever is working on UI has to use IntelliJ Ultimate edition (should be free if you use university email address), this is because the SwingUI designer is very easy to use in IntelliJ (drag/drop buttons) but extremely difficult to use in any other IDE. I would recommend everyone uses IntelliJ anyways since it is the only IDE that lets connect to Github and code on the branch, if you use another IDE you will have to copy and paste your code into the branches manually.

Main branch files:

Object:
- Runway - Java class for a runway object, should have specific parameters (see project spec)
- Aircraft - Java class for an aircraft object, should have specific parameters (see project spec)

Logic:
- Controller - Manages the interaction between the objects (Runway/Aircraft) and the UI. It should be able to create stats, manage queues (holding queue), generate random trafic and manage runway states

UI:
- Should be able to create a UI that is able to communicate with Controller. UI should be able to take user inputs and pass them to Controller and Controller should be able to pass data to display on the UI.

Entire code base should be in Java.
