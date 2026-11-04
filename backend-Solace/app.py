import os
import json
import sqlite3
from contextlib import contextmanager
from datetime import date
from flask import Flask, jsonify, render_template, send_from_directory, request

# 1. Resolve paths to frontend-Solace
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "frontend-Solace"))
TEMPLATES_DIR = os.path.join(FRONTEND_DIR, "templates")

# Auto-detect CSS directory
if os.path.exists(os.path.join(FRONTEND_DIR, "static", "css", "styles.css")):
    STATIC_DIR = os.path.join(FRONTEND_DIR, "static", "css")
elif os.path.exists(os.path.join(FRONTEND_DIR, "static", "styles.css")):
    STATIC_DIR = os.path.join(FRONTEND_DIR, "static")
else:
    STATIC_DIR = FRONTEND_DIR

app = Flask(
    __name__,
    template_folder=TEMPLATES_DIR,
    static_folder=STATIC_DIR,
    static_url_path="/static"
)

DATABASE = os.path.join(CURRENT_DIR, "solace.db")

@contextmanager
def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    with get_db() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT NOT NULL,
            therapist TEXT NOT NULL, client_email TEXT NOT NULL DEFAULT 'client@solace.com', date TEXT NOT NULL, time TEXT NOT NULL,
            session_type TEXT NOT NULL DEFAULT 'Online consultation',
            status TEXT NOT NULL DEFAULT 'Pending', notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
        db.execute("""CREATE TABLE IF NOT EXISTS profiles (
            role TEXT PRIMARY KEY, data TEXT NOT NULL)""")
        columns = {row["name"] for row in db.execute("PRAGMA table_info(appointments)")}
        if "client_email" not in columns:
            db.execute("ALTER TABLE appointments ADD COLUMN client_email TEXT NOT NULL DEFAULT 'client@solace.com'")
        if not db.execute("SELECT 1 FROM appointments LIMIT 1").fetchone():
            sample_rows = [
                ("Anonymous User #6767", "client6767@example.com", "2026-11-06", "9:00 AM", "Confirmed"),
                ("Anonymous User #854", "client854@example.com", "2026-11-06", "10:30 AM", "Cancelled"),
                ("Anonymous User #1234", "client1234@example.com", "2026-11-07", "2:00 PM", "Confirmed"),
                ("Anonymous User #2468", "client2468@example.com", "2026-11-08", "11:00 AM", "Confirmed"),
                ("Anonymous User #5167", "client5167@example.com", "2026-11-09", "1:30 PM", "Pending"),
                ("Anonymous User #3247", "client3247@example.com", "2026-11-10", "3:00 PM", "Confirmed"),
                ("Anonymous User #2048", "client2048@example.com", "2026-11-11", "9:30 AM", "Pending"),
                ("Anonymous User #9876", "client9876@example.com", "2026-11-12", "4:00 PM", "Pending"),
            ]
            db.executemany("INSERT INTO appointments (client, client_email, therapist, date, time, status) VALUES (?, ?, 'Dr. Rizzler6767', ?, ?, ?)", sample_rows)

init_db()

# Serves styles.css whenever href="styles.css" is called
@app.route("/styles.css")
@app.route("/<path:subpath>/styles.css")
def serve_css(subpath=None):
    return send_from_directory(STATIC_DIR, "styles.css")

# ==========================================
# 1. CLIENT ROUTES
# ==========================================
@app.route("/")
@app.route("/client")
def client_dashboard():
    user = {"name": "Binibirocha", "display_name": "User, name", "role": "Client"}
    return render_template("index.html", role="client", active_tab="dashboard", user=user)

@app.route("/search-therapist")
def search_therapist():
    therapists = [
        {"name": "Dr. Zayne Li", "title": "Licensed Therapist", "bio": "Specializes in cognitive behavioral therapy and anxiety."},
        {"name": "Dr. Sarah Chen", "title": "Clinical Psychologist", "bio": "Specializes in stress reduction and emotional wellness."},
        {"name": "Dr. Nyen", "title": "Mindfulness Practitioner", "bio": "Helping clients navigate personal development and therapy."},
        {"name": "Dr. Shaun Murphy", "title": "Behavioral Specialist", "bio": "Experienced clinical psychologist focusing on youth & adult health."},
        {"name": "Dr. Elena Gilbert", "title": "Family Counselor", "bio": "Dedicated to creating safe, empathetic spaces for holistic healing."},
        {"name": "Dr. Alex Grey", "title": "Relationship Therapist", "bio": "Compassionate mental health professional with 10+ years experience."}
    ]
    return render_template("search-therapist.html", therapists=therapists)

@app.route("/schedule")
def client_schedule():
    return render_template("schedule.html")

@app.route("/chats")
def client_chats():
    return render_template("chats.html")

# ==========================================
# 2. THERAPIST ROUTES
# ==========================================
@app.route("/therapist")
@app.route("/therapist/dashboard")
def therapist_dashboard():
    user = {"name": "Dr. Rizzler6767", "display_name": "User, name", "role": "Therapist"}
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
    return render_template("index.html", role="therapist", active_tab="dashboard", user=user, calendar_days=calendar_days, notifications=notifications)

@app.route("/therapist/sessions")
@app.route("/therapist/clients")
@app.route("/therapist/schedule")
@app.route("/therapist/history")
def therapist_subpages():
    # Keep therapist in view with tab highlighted
    return therapist_dashboard()

@app.route("/therapist/bookings")
def therapist_bookings():
    with get_db() as db:
        bookings = [dict(row) for row in db.execute("SELECT * FROM appointments ORDER BY date, time")]
    for item in bookings:
        item["display_date"] = _format_appointment_date(item["date"])
    return render_template("index.html", role="therapist", active_tab="bookings", bookings=bookings,
                           user={"name": "Dr. Rizzler6767", "display_name": "User, name", "role": "Therapist"})

@app.route("/therapist/appointments")
def therapist_appointments():
    with get_db() as db:
        appointments = [dict(row) for row in db.execute(
            "SELECT * FROM appointments ORDER BY date, time")]
        stats = {
            "upcoming": db.execute("SELECT COUNT(*) FROM appointments WHERE status = 'Confirmed' AND date >= ?", (date.today().isoformat(),)).fetchone()[0],
            "pending": db.execute("SELECT COUNT(*) FROM appointments WHERE status = 'Pending'").fetchone()[0],
            "active_users": db.execute("SELECT COUNT(DISTINCT client) FROM appointments WHERE status != 'Cancelled'").fetchone()[0],
            "next_session": next((f"{item['time']}" for item in appointments if item["status"] == "Confirmed" and item["date"] >= date.today().isoformat()), "—"),
        }
    for item in appointments:
        item["display_date"] = _format_appointment_date(item["date"])
    return render_template("index.html", role="therapist", active_tab="appointments",
                           user={"name": "Dr. Rizzler6767", "display_name": "User, name", "role": "Therapist"},
                           appointments=appointments, stats=stats)

def _format_appointment_date(value):
    try:
        day = date.fromisoformat(value)
        return f"{day.strftime('%B')} {day.day}, {day.year}"
    except (TypeError, ValueError):
        return value

@app.route("/api/appointments", methods=["GET", "POST"])
def appointments_api():
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        required = ("client", "therapist", "date", "time")
        if any(not str(payload.get(key, "")).strip() for key in required):
            return jsonify(error="Client, therapist, date, and time are required."), 400
        with get_db() as db:
            cursor = db.execute("INSERT INTO appointments (client, client_email, therapist, date, time, session_type) VALUES (?, ?, ?, ?, ?, ?)",
                (str(payload["client"]).strip(), str(payload.get("client_email", "client@solace.com")).strip(), str(payload["therapist"]).strip(), str(payload["date"]).strip(), str(payload["time"]).strip(), str(payload.get("session_type", "Online consultation"))))
            created = dict(db.execute("SELECT * FROM appointments WHERE id = ?", (cursor.lastrowid,)).fetchone())
        return jsonify(created), 201
    role = request.args.get("role", "client")
    name = request.args.get("name")
    field = "therapist" if role == "therapist" else "client"
    with get_db() as db:
        rows = db.execute(f"SELECT * FROM appointments WHERE {field} = ? ORDER BY date, time", (name or ("Dr. Rizzler6767" if role == "therapist" else "Binibirocha"),))
        return jsonify([dict(row) for row in rows])

@app.route("/api/appointments/<int:appointment_id>", methods=["PATCH"])
def update_appointment(appointment_id):
    payload = request.get_json(silent=True) or {}
    status = payload.get("status")
    if status not in ("Pending", "Confirmed", "Completed", "Cancelled"):
        return jsonify(error="Invalid appointment status."), 400
    with get_db() as db:
        cursor = db.execute("UPDATE appointments SET status = ? WHERE id = ?", (status, appointment_id))
        if not cursor.rowcount:
            return jsonify(error="Appointment not found."), 404
    return jsonify(id=appointment_id, status=status)

@app.route("/api/profile/<role>", methods=["GET", "PUT"])
def profile_api(role):
    defaults = {
        "client": {"name":"CalmCloud27", "email":"Client@example.com", "profile_type":"Anonymous Profile", "bio":"I enjoy quiet moments, meaningful conversations, and finding small ways to grow each day. I’m using Solace to make space for my wellbeing and connect with the right support.", "privacy":"Anonymous to other users", "timezone":"Asia/Manila", "contact_preference":"Email"},
        "therapist": {"name":"Dr. BBno$", "email":"Therapist@example.com", "title":"Psychologist", "bio":"No introduction added yet. Let clients know a little about your approach and the support you offer.", "education":"Doctorate in Clinical Psychology", "specialty":"Psychological wellness", "certifications":"Licensed professional", "availability":"Online and in person", "license":"", "session_format":"Online and in person"},
        "admin": {"name":"Solace Administrator", "email":"admin@solace.com", "title":"System Administrator", "bio":"Responsible for keeping the Solace community safe, supportive, and running smoothly.", "department":"Trust and Safety", "access_level":"Full platform administration", "security_status":"Two-step verification enabled", "notification_email":True, "notification_security":True, "notification_reports":True}
    }
    if role not in defaults:
        return jsonify(error="Unknown profile role."), 404
    with get_db() as db:
        row = db.execute("SELECT data FROM profiles WHERE role = ?", (role,)).fetchone()
        data = {**defaults[role], **(json.loads(row["data"]) if row else {})}
        if request.method == "PUT":
            payload = request.get_json(silent=True) or {}
            data.update({key: value for key, value in payload.items() if key in defaults[role]})
            db.execute("INSERT INTO profiles (role, data) VALUES (?, ?) ON CONFLICT(role) DO UPDATE SET data=excluded.data", (role, json.dumps(data)))
    return jsonify(data)

# ==========================================
# 3. ADMIN ROUTES
# ==========================================
@app.route("/admin")
@app.route("/admin/dashboard")
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
    return render_template("index.html", role="admin", active_tab="dashboard", user=user, stats=stats, pending_verifications=pending_verifications, recent_reports=recent_reports)

@app.route("/admin/therapist-verification")
def admin_therapist_verification():
    return render_template("admin-therapist-verification.html")

@app.route("/admin/user-management")
def admin_user_management():
    return render_template("admin-user-management.html")

@app.route("/admin/reports")
def admin_reports():
    return render_template("admin-reports.html")

# ==========================================
# 4. SHARED PROFILE & SETTINGS
# ==========================================
@app.route("/profile")
def user_profile():
    role = request.args.get("role", "client").lower()
    if role not in ("client", "therapist", "admin"):
        role = "client"
    defaults = {"client": {"name":"CalmCloud27", "email":"Client@example.com", "profile_type":"Anonymous Profile", "bio":"I enjoy quiet moments, meaningful conversations, and finding small ways to grow each day. I’m using Solace to make space for my wellbeing and connect with the right support.", "privacy":"Anonymous to other users", "timezone":"Asia/Manila", "contact_preference":"Email"},
                "therapist": {"name":"Dr. BBno$", "email":"Therapist@example.com", "title":"Psychologist", "bio":"No introduction added yet. Let clients know a little about your approach and the support you offer.", "education":"Doctorate in Clinical Psychology", "specialty":"Psychological wellness", "certifications":"Licensed professional", "availability":"Online and in person", "license":"", "session_format":"Online and in person"},
                "admin": {"name":"Solace Administrator", "email":"admin@solace.com", "title":"System Administrator", "bio":"Responsible for keeping the Solace community safe, supportive, and running smoothly.", "department":"Trust and Safety", "access_level":"Full platform administration", "security_status":"Two-step verification enabled", "notification_email":True, "notification_security":True, "notification_reports":True}}
    with get_db() as db:
        row = db.execute("SELECT data FROM profiles WHERE role = ?", (role,)).fetchone()
    profile = {**defaults[role], **(json.loads(row["data"]) if row else {})}
    user = {"name": profile["name"], "display_name": profile["name"], "role": "Administrator" if role == "admin" else role.capitalize()}
    return render_template("index.html", role=role, active_tab="profile", user=user, profile=profile)

@app.route("/settings")
def user_settings():
    role = request.args.get("role", "client")
    user = {"name": "Binibirocha" if role == "client" else "Dr. Rizzler6767", "display_name": "User, name", "role": role.capitalize()}
    return render_template("index.html", role=role, active_tab="settings", user=user)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
