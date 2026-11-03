import os
from flask import Flask, render_template, send_from_directory, request

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
    role = request.args.get("role", "client")
    user = {"name": "Binibirocha" if role == "client" else "Dr. Rizzler6767", "display_name": "User, name", "role": role.capitalize()}
    return render_template("index.html", role=role, active_tab="profile", user=user)

@app.route("/settings")
def user_settings():
    role = request.args.get("role", "client")
    user = {"name": "Binibirocha" if role == "client" else "Dr. Rizzler6767", "display_name": "User, name", "role": role.capitalize()}
    return render_template("index.html", role=role, active_tab="settings", user=user)

if __name__ == "__main__":
    app.run(debug=True, port=5000)