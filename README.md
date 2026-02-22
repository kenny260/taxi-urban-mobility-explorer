## TAXI-URBAN-MOBILITY-EXPLORER
# Project Overview

Taxi Urban Mobility Explorer is a full-stack data analytics system built to analyze NYC Yellow Taxi trip data. The system allows users to explore revenue distribution, trip volume trends, and busiest pickup-dropoff routes through a web dashboard. The backend exposes REST API endpoints, the database stores structured trip data, and the frontend visualizes results using charts.

# Our Project Links 

- Demo Video: [Insert Demo Video Link Here]
- Team Sheet: [https://docs.google.com/spreadsheets/d/1CcPA_Nx1QI9QoHH6m04kWU8KfAFuQOBvJJqxml7IZqs/edit?usp=sharing]
- Technical Documentation Report: [https://docs.google.com/document/d/1gS8jSFAX83OzD_r73njuk386phhWOhr6-6O-Z-VsYR0/edit?usp=sharing]

# Project Structure
TAXI-URBAN-MOBILITY-EXPLORER/
│
├── backend/
│   ├── api/
│   │   └── routes/
│   │       ├── stats.py
│   │       ├── trips.py
│   │       └── zones.py
│   ├── tests/
│   │   └── test_api.py
│   ├── algorithm.py
│   ├── algorithm_documentation.md
│   ├── app.py
│   ├── database.py
│   └── requirements.txt
│
├── data_pipeline/
│
├── data/
│
├── database/
│   ├── fix_dates.py
│   ├── insert_data.py
│   └── schema.sql
│
├── docs/
│   └── er_diagram.txt
│
├── frontend/
│   └── index.html
│
└── README.md

# System Architecture

* The system follows a three-layer architecture:

- Frontend: Built using HTML, CSS, and JavaScript. It handles user interaction and sends HTTP requests to the backend.
- Backend: Built using Flask. It defines API endpoints grouped into modular route files.
- Database: PostgreSQL database storing trip and zone data using relational tables.

Data flow: User → Frontend → Backend API → PostgreSQL → Backend → Frontend → User.

# Requirements

Before running the project, ensure you have:
Python 3.9 or higher
PostgreSQL installed and running
pip
Git

# Installation and Setup
* Step 1: Clone the Repository

- Open a terminal and run:
git clone https://github.com/kenny260/taxi-urban-mobility-explorer.git
cd TAXI-URBAN-MOBILITY-EXPLORER

* Step 2: Database Setup

- Open PostgreSQL and create the database:
CREATE DATABASE taxi_urban_mobility;

- Connect to it:
\c taxi_urban_mobility

- Run the schema file:
\i database/schema.sql

This will create all required tables.

* Step 3: Insert Data

- Navigate to the database folder:
cd database

Update database credentials inside insert_data.py if necessary. Then run:
python insert_data.py

If required, run:
python fix_dates.py

Ensure that your PostgreSQL server is running before executing these scripts.

* Step 4: Backend Setup

Navigate to the backend folder:
cd backend

Create a virtual environment:
python -m venv venv

Activate the environment:
Windows:
venv\Scripts\activate
Mac/Linux:
source venv/bin/activate

Install dependencies:
pip install -r requirements.txt

* Step 5: Configure Database Connection

Open backend/database.py and update the database credentials to match your PostgreSQL configuration (host, database name, username, password). Save the file.

* Step 6: Run the Backend Server

From inside the backend folder, run:
python app.py

The backend server should start at:
http://127.0.0.1:5000

You can test API endpoints directly in the browser.

* Step 7: Run the Frontend

Navigate to the frontend folder:
cd frontend

Open index.html directly in your browser, or run a simple local server:
python -m http.server 5500

Then open:
http://localhost:5500

Ensure that the API URLs inside your JavaScript match the backend server address.

Running Tests

To run backend tests:
cd backend/tests
python test_api.py

This validates that the API endpoints are working correctly.

# Custom Algorithm

The project includes a manually implemented sorting algorithm located in backend/algorithm.py. This algorithm ranks the busiest pickup-dropoff routes without using built-in sorting functions. Full explanation and complexity analysis are provided in backend/algorithm_documentation.md.

# Troubleshooting

If the backend cannot connect to the database, verify PostgreSQL is running and credentials are correct.
If data is missing, confirm that insert_data.py executed successfully.
If charts do not load, ensure the backend server is running and check browser console for API errors.