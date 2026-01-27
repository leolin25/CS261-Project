# Airport Modelling Project

These instructions are to setup the project on your own computer.

## Step 1: Install Required Tools (If you don't have them)

**1. Install Python**
* Download specific version 3.10 or newer: https://www.python.org/downloads/
* **IMPORTANT:** During installation, check the box that says **"Add Python to PATH"**.

**2. Install Git (For Windows Users)**
* Download here: https://git-scm.com/download/win
* Install with all default settings.
* Once installed, open your Start Menu and search for "Git Bash". Use this terminal for all the commands below.

---

## Step 2: Download the Code

1.  Open your Git Bash terminal
2.  Navigate to where you want the project (e.g., Documents):
    ```bash
    cd ~/Documents
    ```
3.  Clone the repository:
    ```bash
    git clone <PASTE_YOUR_GITHUB_REPO_URL_HERE>
    ```
4.  Enter the project folder:
    ```bash
    cd <YOUR_PROJECT_FOLDER_NAME>
    ```

## Step 3: Set Up the Environment (Do this once)

We need to create a virtual "box" (venv) for our libraries so they don't mess up your computer.

1. Create the Virtual Environment:
```bash
python -m venv venv
```

2. Activate the environment:
```bash
source venv/Scripts/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```
4. Build your own copy of the database:
```bash
cd src
python manage.py migrate
```

----------------------------------------------------------------------------------
STEP 4: RUN THE SIMULATION (Do this every time you work on the project)
-------------------------------------------------------

1. Open your terminal (Git Bash).

2. Navigate to your project folder:
   cd ~/Documents/<YOUR_PROJECT_FOLDER_NAME>

3. Turn on the virtual environment:
   source venv/Scripts/activate

   (IMPORTANT: Check that you see "(venv)" at the start of the line. 
   If you don't see it, the next commands will fail.)

4. Go into the source folder:
   cd src

5. Start the server:
   python manage.py runserver

6. Open the simulation:
   Go to your web browser and enter this address:
   http://127.0.0.1:8000/

   (To stop the server when you are done, press CTRL + C in the terminal).
