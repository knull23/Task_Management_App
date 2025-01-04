from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, date
from collections import defaultdict
import smtplib
import os
import threading
import time
from dotenv import load_dotenv
load_dotenv()

MY_EMAIL = os.getenv("MY_EMAIL")
MY_PASSWORD = os.getenv("MY_PASSWORD")
# ---------------------------
# App Configuration
# ---------------------------
app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# ---------------------------
# Database Models
# ---------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    tasks = db.relationship('Task', backref='user', lazy=True)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    priority = db.Column(db.String(10), default='Low')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    completed_date = db.Column(db.DateTime, nullable=True)
    is_deleted = db.Column(db.Boolean, default=False)


# ---------------------------
# Utility Functions
# ---------------------------
def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return db.session.get(User, user_id)
    return None


# ---------------------------
# Routes
# ---------------------------
@app.route('/')
def home():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


# User Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'danger')
            return redirect(url_for('register'))

        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        send_welcome_email(email)
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


def send_welcome_email(user_email):
    subject = "Welcome to Our App!"
    body = """
    Hi there,

    Thank you for registering with us! We're excited to have you on board.

    Best regards,
    The Team
    """

    # Craft the email message
    email_message = f"Subject: {subject}\n\n{body}"

    try:
        # Set up the connection to Gmail SMTP server
        with smtplib.SMTP("smtp.gmail.com", 587) as connection:
            connection.starttls()  # Secure the connection
            connection.login(MY_EMAIL, MY_PASSWORD)
            connection.sendmail(
                from_addr=MY_EMAIL,
                to_addrs=user_email,
                msg=email_message
            )
        print(f"Welcome email sent to {user_email}!")
    except Exception as e:
        print(f"Error while sending welcome email: {e}")


# -----------------------------
# 📧 Function to Send an Email
# -----------------------------
def send_email(subject, body, recipient):
    email_message = f"Subject: {subject}\n\n{body}"
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as connection:
            connection.starttls()
            connection.login(MY_EMAIL, MY_PASSWORD)
            connection.sendmail(from_addr=MY_EMAIL, to_addrs=recipient, msg=email_message)
        print(f"✅ Email sent to {recipient}")
    except smtplib.SMTPAuthenticationError:
        print("❌ Authentication Error: Check your email credentials.")
    except smtplib.SMTPException as e:
        print(f"❌ SMTP Error: {e}")
    except Exception as e:
        print(f"❌ General Error: {e}")


# -----------------------------------------------
# 📅 Function to Send Emails for Due & Overdue Tasks
# -----------------------------------------------
def send_due_date_emails():
    with app.app_context():
        try:
            today = datetime.now().date()

            # Fetch tasks that are due today and still pending
            tasks_due_today = Task.query.filter_by(due_date=today, status='Pending').all()

            # Fetch tasks that are overdue and still pending
            tasks_overdue = Task.query.filter(Task.due_date < today, Task.status == 'Pending').all()

            if not tasks_due_today and not tasks_overdue:
                print("ℹ️ No tasks due or overdue today.")
                return

            # Process tasks due today
            for task in tasks_due_today:
                user = User.query.get(task.user_id)
                if user:
                    subject = f"Task Due Today: {task.title}"
                    body = (
                        f"Hi {user.username},\n\n"
                        f"This is a friendly reminder that your task '{task.title}' is due today.\n"
                        f"Please make sure to complete it before the end of the day.\n\n"
                        f"Best regards,\nTask Management Team"
                    )
                    send_email(subject, body, user.email)
                    print(f"📧 Due Email sent for Task ID: {task.id} to {user.email}")

            # Process overdue tasks
            for task in tasks_overdue:
                user = User.query.get(task.user_id)
                if user:
                    subject = f"Task Overdue: {task.title}"
                    body = (
                        f"Hi {user.username},\n\n"
                        f"This is a reminder that your task '{task.title}' was due on {task.due_date}.\n"
                        f"Please address this task as soon as possible.\n\n"
                        f"Best regards,\nTask Management Team"
                    )
                    send_email(subject, body, user.email)
                    print(f"📧 Overdue Email sent for Task ID: {task.id} to {user.email}")

        except Exception as e:
            print(f"❌ Error while processing due/overdue emails: {e}")


# --------------------------------------
# ⏰ Scheduler for Daily Email Notifications
# --------------------------------------
def schedule_daily_emails():
    print("⏳ Email scheduler started...")
    last_run_date = None  # Track the last run date to prevent duplicate sends

    while True:
        current_time = datetime.now()
        current_date = current_time.date()

        # Check if it's time to send emails (8:00 AM daily) and not already sent today
        if current_time.hour == 8 and current_time.minute == 0 and last_run_date != current_date:
            print("📤 Triggering daily due and overdue task email notifications...")
            send_due_date_emails()
            last_run_date = current_date  # Update the last run date
            time.sleep(61)  # Wait 61 seconds to avoid multiple triggers within the same minute

        time.sleep(30)  # Check every 30 seconds


# --------------------------------------------------
# 🚀 Start the Background Email Scheduler in a Thread
# --------------------------------------------------
email_scheduler = threading.Thread(target=schedule_daily_emails, daemon=True)
email_scheduler.start()
print("✅ Email scheduler thread started successfully.")


# -----------------------------------
# 🛠️ Test Email Function (Optional)
# -----------------------------------
# Uncomment this line to send a test email manually.
# send_email("Test Email", "This is a test email from your scheduler.", "your_email@example.com")

# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if email and password are provided
        if not email or not password:
            flash('Please enter both email and password.', 'warning')
            return render_template('login.html')

        user = User.query.filter_by(email=email).first()

        # Validate user and password
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))

        # Invalid credentials
        flash('Invalid email or password. Please try again.', 'danger')

    return render_template('login.html')


# User Dashboard
@app.route('/dashboard')
def dashboard():
    user = get_current_user()
    if not user:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))

    tasks = Task.query.filter_by(user_id=user.id).all()
    pending_tasks = sum(1 for task in tasks if task.status == 'Pending' and not task.is_deleted)
    completed_tasks = sum(1 for task in tasks if task.status == 'Completed')
    total_tasks = pending_tasks + completed_tasks

    return render_template('dashboard.html',
                           tasks=tasks,
                           pending_tasks=pending_tasks,
                           completed_tasks=completed_tasks,
                           total_tasks=total_tasks,
                           username=user.username)


# Create Task
@app.route('/task/create', methods=['GET', 'POST'])
def create_task():
    user = get_current_user()
    if not user:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description')
        due_date = request.form['due_date']
        priority = request.form.get('priority', 'Low')

        task = Task(
            title=title,
            description=description,
            due_date=datetime.strptime(due_date, '%Y-%m-%d'),
            priority=priority,
            user_id=user.id
        )
        db.session.add(task)
        db.session.commit()
        flash('Task created successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('create_task.html')


# Mark Task as Completed
@app.route('/task/<int:task_id>/complete', methods=['POST'])
def complete_task(task_id):
    user = get_current_user()
    if not user:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))

    task = Task.query.get_or_404(task_id)
    task.status = 'Completed'
    task.completed_date = datetime.utcnow()
    db.session.commit()
    flash('Task marked as completed!', 'success')
    return redirect(url_for('dashboard'))


# Delete Task Route
@app.route('/delete_task/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    user = get_current_user()
    if not user:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))

    task = Task.query.filter_by(id=task_id, user_id=user.id, status='Completed').first()
    if task:
        # Mark the task as deleted instead of removing it
        task.is_deleted = True
        db.session.commit()
        flash('Task has been removed from Dashboard and Calendar.', 'success')
    else:
        flash('Task not found or not marked as completed.', 'error')

    return redirect(url_for('dashboard'))


@app.route('/calendar')
def calendar():
    user = get_current_user()  # Assuming this gets the current user
    if not user:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))

    # Fetch tasks from the database
    tasks = Task.query.filter_by(user_id=user.id, is_deleted=False, status='Pending').all()

    # Prepare events for the calendar
    events = []
    for task in tasks:
        if task.due_date:
            event = {
                'title': task.title,
                'start': task.due_date.strftime('%Y-%m-%d'),
                'description': task.description,
                'priority': task.priority
            }
            events.append(event)

    # Handle month and year navigation
    year = int(request.args.get('year', datetime.now().year))
    month = int(request.args.get('month', datetime.now().month))
    today = datetime.now()

    # Calculate the first and last day of the month
    month_start = datetime(year, month, 1)
    next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
    month_end = next_month - timedelta(days=1)

    calendar_days = []

    # Group tasks by their due date
    tasks_by_date = defaultdict(list)
    for task in tasks:
        if task.due_date:
            tasks_by_date[task.due_date].append(task)

    # Generate days for the current month
    current_day = month_start
    while current_day <= month_end:
        tasks_for_day = tasks_by_date.get(current_day.date(), [])
        calendar_days.append({
            'date': current_day.strftime('%Y-%m-%d'),
            'day': current_day.strftime('%d'),
            'is_today': current_day.date() == today.date(),
            'tasks': [{
                'title': task.title,
                'priority': task.priority,
                'description': task.description
            } for task in tasks_for_day]
        })
        current_day += timedelta(days=1)

    # Month navigation logic
    prev_month = (month_start - timedelta(days=1)).month
    prev_year = (month_start - timedelta(days=1)).year
    next_month = (month_end + timedelta(days=1)).month
    next_year = (month_end + timedelta(days=1)).year

    return render_template(
        'calendar.html',
        events=events,
        calendar_days=calendar_days,
        current_year=year,
        current_month=month,
        prev_year=prev_year,
        prev_month=prev_month,
        next_year=next_year,
        next_month=next_month
    )


# Achievement View
@app.route('/achievement')
def achievement():
    user = get_current_user()
    if not user:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))

    tasks = Task.query.filter_by(user_id=user.id).all()
    pending_tasks = [task for task in tasks if task.status == 'Pending' and not task.is_deleted]
    completed_tasks = [task for task in tasks if task.status == 'Completed']
    total_tasks = len(pending_tasks) + len(completed_tasks)

    # Extract titles of completed tasks
    completed_task_titles = [task.title for task in completed_tasks]

    # Early completed tasks
    early_tasks = [
        task for task in completed_tasks
        if task.completed_date and task.due_date and task.completed_date.date() < task.due_date
    ]

    # Completion Rate
    completion_rate = round((len(completed_tasks) / total_tasks) * 100, 2) if total_tasks else 0

    # Streak Logic (Current Streak & Max Streak)
    streak = 0
    max_streak = 0

    today = date.today()
    previous_date = today

    # Sort completed tasks by completed_date
    sorted_completed_tasks = sorted(
        [task for task in completed_tasks if task.completed_date],
        key=lambda task: task.completed_date
    )

    current_streak = 0

    for i, task in enumerate(sorted_completed_tasks):
        task_date = task.completed_date.date()

        if i == 0 or task_date == previous_date - timedelta(days=1):
            current_streak += 1
            streak = current_streak
        else:
            current_streak = 1  # Reset current streak if gap is found

        previous_date = task_date
        max_streak = max(max_streak, current_streak)

    return render_template(
        'achievement.html',
        total_tasks=total_tasks,
        completed_task_titles=completed_task_titles,
        completed_tasks=len(completed_tasks),
        completion_rate=completion_rate,
        early_tasks=early_tasks,
        streak=streak,
        max_streak=max_streak
    )

@app.route('/analytics')
def analytics():
    user = get_current_user()
    if not user:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))

    tasks = Task.query.filter_by(user_id=user.id).all()

    # Priority counts
    priority_counts = {
        'Low': sum(1 for task in tasks if task.priority == 'Low' and not task.is_deleted),
        'Medium': sum(1 for task in tasks if task.priority == 'Medium' and not task.is_deleted),
        'High': sum(1 for task in tasks if task.priority == 'High' and not task.is_deleted)
    }

    # Task status counts
    pending_tasks = [task for task in tasks if task.status == 'Pending' and not task.is_deleted]
    completed_tasks = [task for task in tasks if task.status == 'Completed']
    overdue_tasks = sum(1 for task in tasks if task.status == 'Pending' and task.due_date < datetime.now().date())

    # Pass only pending tasks visible on the dashboard
    recent_tasks = [task for task in pending_tasks if not task.is_deleted]

    return render_template(
        'analytics.html',
        priority_counts=priority_counts,
        pending_tasks=len(pending_tasks),
        completed_tasks=len(completed_tasks),
        overdue_tasks=overdue_tasks,
        recent_tasks=recent_tasks  # Only valid pending tasks
    )


# Logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('home'))


# ---------------------------
# Run Application
# ---------------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)



# the day of due date, user will receive an email
# professional level css
# make ui interface more effiecnt and good