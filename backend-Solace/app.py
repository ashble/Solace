import os
from flask import Flask, render_template

# 1. Resolve the path to frontend/templates
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "frontend-Solace", "templates"))
STATIC_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "frontend", "static"))
app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR)

# Debug prints to see exactly what Flask sees:
print(f"Looking for templates in: {TEMPLATES_DIR}")
if os.path.exists(TEMPLATES_DIR):
    print("Files found in templates folder:", os.listdir(TEMPLATES_DIR))
else:
    print("❌ ERROR: Folder does not exist at:", TEMPLATES_DIR)

app = Flask(
    __name__,
    template_folder=TEMPLATES_DIR,
    static_folder=STATIC_DIR
)

@app.route("/")
@app.route("/client")
def client_dashboard():
    user = {"name": "Binibirocha", "display_name": "User, name", "role": "Client"}
    appointment = {
        "title": "Upcoming Appointment",
        "time": "Today, 3:00-4:30 PM",
        "doctor": "Dr. Skibidi Quack quack"
    }
    # Use exact filename (hyphen or underscore):
    return render_template("client-dashboard.html", user=user, appointment=appointment)

@app.route("/therapist")
def therapist_dashboard():
    user = {"name": "Dr. Rizzler6767", "display_name": "User, name", "role": "Client"}
    meeting = {"title": "Upcoming Meeting", "time": "Today, 3:00-4:30 PM", "client": "Anonymous#1736"}
    calendar_days = [
        {"day": "Mon", "date": 19}, {"day": "Tue", "date": 20}, {"day": "Wed", "date": 21},
        {"day": "Thur", "date": 22}, {"day": "Fri", "date": 23}, {"day": "Sat", "date": 24},
        {"day": "Sun", "date": 25}, {"day": "Mon", "date": 26}, {"day": "Tue", "date": 27},
        {"day": "Wed", "date": 28}, {"day": "Thur", "date": 29}, {"day": "Fri", "date": 30},
        {"day": "Sat", "date": 31}, {"day": "Sun", "date": 1}, {"day": "Mon", "date": 2},
        {"day": "Tue", "date": 3, "active": True},
        {"day": "Wed", "date": 4}, {"day": "Thur", "date": 5}, {"day": "Fri", "date": 6}
    ]
    notifications = [
        {"id": "Anonymous#1736", "duration": "1h 14m 20s session", "status": "Approved", "type": "purple"},
        {"id": "Anonymous#5167", "duration": "47 minute session", "status": "In Progress", "type": "peach"},
        {"id": "Anonymous#3247", "duration": "30 minute session", "status": "Pending", "type": "yellow"}
    ]
    return render_template("therapist-dashboard.html", user=user, meeting=meeting, calendar_days=calendar_days, notifications=notifications)

@app.route("/admin")
def admin_dashboard():
    user = {"name": "Dr. Rizzler6767", "display_name": "User, name", "role": "Administrator"}
    stats = {"total_reports": "12,345", "urgent_reports": "123", "admins_online": "12"}
    pending_verifications = [
        {"name": "Dr. Doofenshmirtz", "date": "October 26, 2026"},
        {"name": "Dr. Eggman", "date": "October 26, 2026"},
        {"name": "Dr. Shaun Murphy", "date": "October 24, 2026"}
    ]
    recent_reports = [
        {"name": "Anonymous User#6767", "date": "October 27, 2026"},
        {"name": "Dr. Eggman", "date": "October 26, 2026"},
        {"name": "Anonymous User#854", "date": "October 24, 2026"}
    ]
    return render_template("admin-dashboard.html", user=user, stats=stats, pending_verifications=pending_verifications, recent_reports=recent_reports)

if __name__ == "__main__":
    app.run(debug=True, port=5000)