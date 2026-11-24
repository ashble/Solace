import os
import json
import sqlite3
import secrets
from contextlib import contextmanager
from datetime import date, datetime
from extensions import db
from auth_helpers import csrf_required, current_user

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
    STATIC_DIR = os.path.join(FRONTEND_DIR, "static")
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

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("COOKIE_SECURE", "false").lower() == "true"

DATABASE = os.path.join(CURRENT_DIR, "solace.db")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL") or ("sqlite:///" + DATABASE.replace("\\", "/"))
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["REPORT_UPLOAD_FOLDER"] = os.path.join(CURRENT_DIR, "uploads", "reports")
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024
db.init_app(app)


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
        for column, definition in {
            "client_id": "INTEGER REFERENCES users(id)",
            "therapist_id": "INTEGER REFERENCES users(id)",
            "scheduled_at": "TEXT",
            "duration_minutes": "INTEGER NOT NULL DEFAULT 50",
            "meeting_link": "TEXT",
            "legacy_booking_id": "INTEGER",
        }.items():
            if column not in columns:
                db.execute(f"ALTER TABLE appointments ADD COLUMN {column} {definition}")
        db.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_appointments_legacy_booking_id ON appointments(legacy_booking_id)")


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
    return send_from_directory(os.path.join(FRONTEND_DIR, "static", "css"), "styles.css")

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


def saved_profile(role, user_id=None):
    if user_id is not None:
        from models import UserProfile
        account_profile = UserProfile.query.filter_by(user_id=user_id).first()
        data = json.loads(account_profile.data) if account_profile else {}
        user = db.session.get(User, user_id)
        return {**PROFILE_DEFAULTS[role], **data,
                "name": user.name if user else PROFILE_DEFAULTS[role]["name"],
                "email": user.email if user else PROFILE_DEFAULTS[role]["email"]}
    with get_db() as db:
        row = db.execute("SELECT data FROM profiles WHERE role = ?", (role,)).fetchone()
    saved_data = json.loads(row["data"]) if row else {}
    return {**PROFILE_DEFAULTS[role], **saved_data}


@app.route("/profile")
def profile_page():
    user_record = current_user()
    if not user_record or user_record.status != "active":
        return jsonify(error="Authentication required."), 401
    role = user_record.role
    if role not in PROFILE_DEFAULTS:
        return jsonify(error="Profile unavailable for this account."), 403
    profile = saved_profile(role, user_record.id)
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
    user_record = current_user()
    if not user_record or user_record.status != "active":
        return jsonify(error="Authentication required."), 401
    role = user_record.role
    if role not in PROFILE_DEFAULTS:
        return jsonify(error="Settings unavailable for this account."), 403
    profile = saved_profile(role, user_record.id)
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
@csrf_required
def update_profile(role):
    if role not in PROFILE_DEFAULTS:
        return jsonify(error="Unknown profile role."), 404
    user_record = current_user()
    if not user_record or user_record.status != "active":
        return jsonify(error="Authentication required."), 401
    if user_record.role != role:
        return jsonify(error="You can only update your own profile."), 403
    payload = request.get_json(silent=True) or {}
    profile = saved_profile(role, user_record.id)
    profile.update({k: v for k, v in payload.items() if k in PROFILE_DEFAULTS[role] and k not in {"email"}})
    from models import UserProfile
    account_profile = UserProfile.query.filter_by(user_id=user_record.id).first()
    if account_profile:
        account_profile.data = json.dumps(profile)
    else:
        account_profile = UserProfile(user_id=user_record.id, data=json.dumps(profile))
        db.session.add(account_profile)
    db.session.commit()
    return jsonify(profile)


# ==========================================
# 5. APPOINTMENT APIS
# ==========================================

# ==========================================
# 6. REGISTER MODULAR BLUEPRINTS
# ==========================================

from routes.client_routes import client_bp
from routes.admin_routes import admin_bp
from routes.therapist_routes import therapist_bp
from routes.report_routes import report_bp
from routes.auth_routes import auth_bp
from routes.booking_routes import booking_bp, legacy_booking_bp
from routes.chat_routes import chat_bp
from models import Appointment, Report, ReportAttachment, User, TherapistVerification

app.register_blueprint(client_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(therapist_bp)
app.register_blueprint(report_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(booking_bp)
app.register_blueprint(legacy_booking_bp)
app.register_blueprint(chat_bp)


def migrate_booking_rows():
    """Copy rows from the former ORM table into appointments without deleting its archive."""
    from sqlalchemy import inspect, text

    changed = False
    for item in Appointment.query.filter(
        (Appointment.client_id.is_(None)) | (Appointment.therapist_id.is_(None)) | (Appointment.scheduled_at.is_(None))
    ).all():
        if item.client_id is None and item.client_email:
            matched_client = User.query.filter(db.func.lower(User.email) == item.client_email.lower()).first()
            if matched_client and matched_client.role == "client":
                item.client_id = matched_client.id
                changed = True
        if item.therapist_id is None and item.therapist_name:
            matched_therapist = User.query.filter(
                db.func.lower(User.name) == item.therapist_name.lower(), User.role == "therapist"
            ).first()
            if matched_therapist:
                item.therapist_id = matched_therapist.id
                changed = True
        if item.scheduled_at is None:
            try:
                item.scheduled_at = datetime.strptime(f"{item.date} {item.time}", "%Y-%m-%d %I:%M %p").isoformat()
                changed = True
            except (TypeError, ValueError):
                pass
    if changed:
        db.session.commit()

    if "booking_appointments" not in inspect(db.engine).get_table_names():
        return
    columns = {column["name"] for column in inspect(db.engine).get_columns("booking_appointments")}
    needed = {"id", "client_id", "therapist_id", "scheduled_at", "duration_minutes", "status", "session_type", "notes", "created_at"}
    if not needed.issubset(columns):
        return
    rows = db.session.execute(text("SELECT * FROM booking_appointments ORDER BY id")).mappings().all()
    for row in rows:
        if Appointment.query.filter_by(legacy_booking_id=row["id"]).first():
            continue
        scheduled = datetime.fromisoformat(str(row["scheduled_at"]).replace("Z", "+00:00"))
        client = db.session.get(User, row["client_id"])
        therapist = db.session.get(User, row["therapist_id"])
        item = Appointment(
            client_id=client.id if client else None,
            therapist_id=therapist.id if therapist else None,
            client_name=client.name if client else f"Client #{row['client_id']}",
            therapist_name=therapist.name if therapist else f"Therapist #{row['therapist_id']}",
            client_email=client.email if client else "client@solace.com",
            date=scheduled.date().isoformat(),
            time=scheduled.strftime("%I:%M %p").lstrip("0"),
            scheduled_at=scheduled.isoformat(),
            duration_minutes=row["duration_minutes"],
            status=str(row["status"]).capitalize(),
            session_type=row["session_type"] or "Online consultation",
            notes=row["notes"] or "",
            legacy_booking_id=row["id"],
        )
        db.session.add(item)
    db.session.commit()


with app.app_context():
    db.create_all()
    migrate_booking_rows()


# ==========================================
# 7. RUN SERVER
# ==========================================

if __name__ == "__main__":
    app.run(debug=True, port=5000)
