import os
import json
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime

from flask import (
    Flask,
    jsonify,
    render_template,
    send_from_directory,
    request,
)

# ==========================================
# 1. DIRECTORY SETUP & APP CONFIG
# ==========================================

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(
    os.path.join(CURRENT_DIR, "..", "frontend-Solace")
)

# Auto-detect templates directory
if os.path.isdir(os.path.join(FRONTEND_DIR, "templates")):
    TEMPLATES_DIR = os.path.join(FRONTEND_DIR, "templates")
else:
    TEMPLATES_DIR = os.path.join(CURRENT_DIR, "templates")

# Auto-detect static/CSS directory
if os.path.isfile(os.path.join(FRONTEND_DIR, "static", "css", "styles.css")):
    STATIC_DIR = os.path.join(FRONTEND_DIR, "static", "css")
elif os.path.isfile(os.path.join(FRONTEND_DIR, "static", "styles.css")):
    STATIC_DIR = os.path.join(FRONTEND_DIR, "static")
elif os.path.isdir(os.path.join(CURRENT_DIR, "static")):
    STATIC_DIR = os.path.join(CURRENT_DIR, "static")
else:
    STATIC_DIR = CURRENT_DIR

app = Flask(
    __name__,
    template_folder=TEMPLATES_DIR,
    static_folder=STATIC_DIR,
    static_url_path="/static",
)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "solace-secret-key-6767"
)

DATABASE = os.path.join(CURRENT_DIR, "solace.db")


# ==========================================
# 2. DATABASE INITIALIZATION & HELPERS
# ==========================================

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
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client TEXT NOT NULL,
                therapist TEXT NOT NULL,
                client_email TEXT NOT NULL DEFAULT 'client@solace.com',
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                session_type TEXT NOT NULL DEFAULT 'Online consultation',
                status TEXT NOT NULL DEFAULT 'Pending',
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                role TEXT PRIMARY KEY,
                data TEXT NOT NULL
            )
            """
        )
        columns = {row["name"] for row in db.execute("PRAGMA table_info(appointments)")}
        if "client_email" not in columns:
            db.execute("ALTER TABLE appointments ADD COLUMN client_email TEXT NOT NULL DEFAULT 'client@solace.com'")


init_db()


def render_first_template(template_list, **context):
    for t in template_list:
        if os.path.isfile(os.path.join(TEMPLATES_DIR, t)):
            return render_template(t, **context)
    return render_template(template_list[-1], **context)


def display_appointment_date(value):
    try:
        parsed = date.fromisoformat(value)
        return f"{parsed.strftime('%B')} {parsed.day}, {parsed.year}"
    except (TypeError, ValueError):
        return value


def appointment_sort_key(date_value, time_value):
    try:
        parsed = datetime.strptime(f"{date_value} {time_value}", "%Y-%m-%d %I:%M %p")
        return parsed.timestamp()
    except (TypeError, ValueError):
        return 0


# ==========================================
# 3. STATIC ASSET SERVERS
# ==========================================

@app.route("/styles.css")
@app.route("/<path:subpath>/styles.css")
def serve_css(subpath=None):
    return send_from_directory(STATIC_DIR, "styles.css")

@app.route("/solace-logo-pnjee.png")
@app.route("/static/solace-logo-pnjee.png")
@app.route("/<path:subpath>/solace-logo-pnjee.png")
def serve_solace_logo(subpath=None):
    for folder in [
        STATIC_DIR,
        os.path.join(FRONTEND_DIR, "static"),
        os.path.join(STATIC_DIR, "css"),
        CURRENT_DIR,
    ]:
        if os.path.isfile(os.path.join(folder, "solace-logo-pnjee.png")):
            return send_from_directory(folder, "solace-logo-pnjee.png")
    return send_from_directory(STATIC_DIR, "solace-logo-pnjee.png")


@app.route("/sean-pages.js")
def serve_sean_page_scripts():
    js_directory = os.path.join(FRONTEND_DIR, "static", "js")
    if os.path.isdir(js_directory) and os.path.isfile(os.path.join(js_directory, "sean-pages.js")):
        return send_from_directory(js_directory, "sean-pages.js")
    return ("", 204)


# ==========================================
# 4. SHARED PROFILE & SETTINGS
# ==========================================

PROFILE_DEFAULTS = {
    "client": {
        "name": "CalmCloud27",
        "email": "Client@example.com",
        "profile_type": "Anonymous Profile",
        "bio": "I enjoy quiet moments, meaningful conversations, and finding small ways to grow each day.",
        "privacy": "Anonymous to other users",
        "timezone": "Asia/Manila",
        "contact_preference": "Email",
    },
    "therapist": {
        "name": "Dr. BBno$",
        "email": "Therapist@example.com",
        "title": "Psychologist",
        "bio": "No introduction added yet.",
        "education": "Doctorate in Clinical Psychology",
        "specialty": "Psychological wellness",
        "certifications": "Licensed professional",
        "availability": "Online and in person",
        "license": "",
        "session_format": "Online and in person",
    },
    "admin": {
        "name": "Solace Administrator",
        "email": "admin@solace.com",
        "title": "System Administrator",
        "bio": "Responsible for keeping the Solace community safe, supportive, and running smoothly.",
        "department": "Trust and Safety",
        "access_level": "Full platform administration",
        "security_status": "Two-step verification enabled",
        "notification_email": True,
        "notification_security": True,
        "notification_reports": True,
    },
}


def saved_profile(role):
    with get_db() as db:
        row = db.execute("SELECT data FROM profiles WHERE role = ?", (role,)).fetchone()
    saved_data = json.loads(row["data"]) if row else {}
    return {**PROFILE_DEFAULTS[role], **saved_data}


@app.route("/profile")
def profile_page():
    role = request.args.get("role", "client").lower()
    if role not in PROFILE_DEFAULTS:
        role = "client"
    profile = saved_profile(role)
    user = {
        "name": profile["name"],
        "display_name": profile["name"],
        "role": "Administrator" if role == "admin" else role.capitalize(),
    }
    templates = {
        "client": ["User-profile.html", "index.html"],
        "therapist": ["Therapist-profile.html", "index.html"],
        "admin": ["Admin-profile.html", "index.html"],
    }
    return render_first_template(
        templates.get(role, ["index.html"]),
        role=role,
        active_page="profile",
        active_tab="profile",
        profile=profile,
        user=user,
    )


@app.route("/settings")
def settings_page():
    role = request.args.get("role", "client").lower()
    if role not in PROFILE_DEFAULTS:
        role = "client"
    profile = saved_profile(role)
    user = {
        "name": profile["name"],
        "display_name": profile["name"],
        "role": "Administrator" if role == "admin" else role.capitalize(),
    }
    return render_template(
        "index.html",
        role=role,
        active_tab="settings",
        active_page="settings",
        profile=profile,
        user=user,
    )


@app.route("/api/profile/<role>", methods=["PUT"])
def update_profile(role):
    if role not in PROFILE_DEFAULTS:
        return jsonify(error="Unknown profile role."), 404
    payload = request.get_json(silent=True) or {}
    profile = saved_profile(role)
    profile.update({k: v for k, v in payload.items() if k in PROFILE_DEFAULTS[role]})
    with get_db() as db:
        db.execute(
            "INSERT INTO profiles (role, data) VALUES (?, ?) ON CONFLICT(role) DO UPDATE SET data = excluded.data",
            (role, json.dumps(profile)),
        )
    return jsonify(profile)


# ==========================================
# 5. APPOINTMENT APIS
# ==========================================

@app.route("/api/appointments", methods=["POST"])
def create_appointment():
    payload = request.get_json(silent=True) or {}
    required_fields = ("client", "therapist", "date", "time")
    if any(not str(payload.get(f, "")).strip() for f in required_fields):
        return jsonify(error="Client, therapist, date, and time are required."), 400

    with get_db() as db:
        cursor = db.execute(
            """
            INSERT INTO appointments (client, client_email, therapist, date, time, session_type)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(payload["client"]).strip(),
                str(payload.get("client_email", "client@solace.com")).strip(),
                str(payload["therapist"]).strip(),
                str(payload["date"]).strip(),
                str(payload["time"]).strip(),
                str(payload.get("session_type", "Online consultation")).strip(),
            ),
        )
        created_row = db.execute("SELECT * FROM appointments WHERE id = ?", (cursor.lastrowid,)).fetchone()
        created = dict(created_row)
    return jsonify(created), 201


@app.route("/api/appointments/<int:appointment_id>", methods=["PATCH"])
def update_appointment(appointment_id):
    payload = request.get_json(silent=True) or {}
    status = payload.get("status")
    if status not in ("Pending", "Confirmed", "Completed", "Cancelled"):
        return jsonify(error="Invalid appointment status."), 400

    with get_db() as db:
        cursor = db.execute("UPDATE appointments SET status = ? WHERE id = ?", (status, appointment_id))
        if cursor.rowcount == 0:
            return jsonify(error="Appointment not found."), 404
    return jsonify(id=appointment_id, status=status)


# ==========================================
# 6. REGISTER MODULAR BLUEPRINTS
# ==========================================

from routes.client_routes import client_bp
from routes.admin_routes import admin_bp
from routes.therapist_routes import therapist_bp

app.register_blueprint(client_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(therapist_bp)


# ==========================================
# 7. RUN SERVER
# ==========================================

if __name__ == "__main__":
    app.run(debug=True, port=5000)