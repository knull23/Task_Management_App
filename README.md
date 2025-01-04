# Task Management - To-Do List Application

It is a simple and user-friendly to-do list application that allows users to create, manage, and organize their tasks effectively. The application is built using Python, Flask, and SQLite, providing a straightforward and reliable way to track your daily tasks.


## Features

- **User Registration & Login:** Users can create an account, log in, and manage their tasks securely.
- **Task Management:** Add, edit, and delete tasks easily.
- **Task Priority:** Assign priorities to tasks to focus on what matters the most.
- **Task Completion:** Mark tasks as complete when done and keep track of completed and pending tasks.
- **Data Persistence:** Tasks are stored in a database, ensuring that your data is saved even after logging out or restarting the app.


## Tech Stack

- **Backend:** Python (Flask)
- **Database:** SQLite
- **Frontend:** HTML, CSS (Bootstrap)
- **Authentication:** Flask-Login


## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/knull23/Task_Management_App.git
   cd Task_Management_App
   ```

2.Create a virtual environment:

   ```bash
   python -m venv venv
   ```

3.Activate the virtual environment:
On Windows:
   ```bash
   venv\Scripts\activate
   ```

On macOS/Linux:
   ```bash
   source venv/bin/activate
   ```

4.Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5.Run the application:
   ```bash
   python app.py
   ```
   Open your browser and go to http://127.0.0.1:5000/ to access the app.


## Usage
  1. Sign up for a new account or log in with existing credentials.
  2. Add new tasks to your to-do list with optional priorities.
  3. Edit or delete tasks as needed.
  4. Mark tasks as completed to track progress.
  5. Helps in maintaining current streak of user
  6. Helps in analyzing tasks divides them into high, medium and low priority 
