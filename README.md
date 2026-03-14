# Airport Modelling Project User Guide

## Step 1. Install Python

Install python onto your computer if you have not already:

https://www.python.org/downloads/

## Step 2: Extract the code 

1. Locate the zip file and extract it

2. Open command prompt

3. Using command prompt navigate to the newly extracted folder

```cmd
cd Documects/CS261-Project
```

## Step 3: Set Up the Environment

You need to create a virtual "box" (venv) for the libraries so they don't mess up your computer.

1. Create the Virtual Environment:
```cmd
python -m venv venv
```

2. Activate the environment:
```cmd
source venv/Scripts/activate
```

3. Install dependencies:
```cmd
pip install -r requirements.txt
```
4. Build your own copy of the database:
```cmd
cd src
python manage.py migrate
```

## STEP 4: RUN THE SIMULATION (Do this every time you want to open the model)

1. Open your terminal/command prompt.

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
