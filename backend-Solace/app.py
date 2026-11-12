import os
import json
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta

from flask import (
    Flask,
    jsonify,
    render_template,
    send_from_directory,
    request,
    redirect,
)


# ==========================================
# 1. DIRECTORY SETUP & APP CONFIG
# ==========================================

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(
    os.path.join(CURRENT_DIR, "..", "frontend-Solace")
)

# Auto-detect the templates directory.
if os.path.isdir(os.path.join(FRONTEND_DIR, "templates")):
    TEMPLATES_DIR = os.path.join(FRONTEND_DIR, "templates")
else:
    TEMPLATES_DIR = os.path.join(CURRENT_DIR, "templates")

# Auto-detect the directory containing styles.css (used by the old pages
# through the /styles.css route below).
if os.path.isfile(os.path.join(FRONTEND_DIR, "static", "css", "styles.css")):
    STATIC_DIR = os.path.join(FRONTEND_DIR, "static", "css")
elif os.path.isfile(os.path.join(FRONTEND_DIR, "static", "styles.css")):
    STATIC_DIR = os.path.join(FRONTEND_DIR, "static")
elif os.path.isdir(os.path.join(CURRENT_DIR, "static")):
    STATIC_DIR = os.path.join(CURRENT_DIR, "static")
else:
    STATIC_DIR = CURRENT_DIR

# The Flask static folder is the whole frontend static directory, so
# url_for('static', filename='css/solace.css') resolves correctly.
if os.path.isdir(os.path.join(FRONTEND_DIR, "static")):
    FLASK_STATIC_DIR = os.path.join(FRONTEND_DIR, "static")
else:
    FLASK_STATIC_DIR = STATIC_DIR

app = Flask(
    __name__,
    template_folder=TEMPLATES_DIR,
    static_folder=FLASK_STATIC_DIR,
    static_url_path="/static",
)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "solace-secret-key-6767"
)

DATABASE = os.path.join(CURRENT_DIR, "solace.db")


# ==========================================
# 2. DATABASE CONNECTION AND INITIALIZATION
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

        # Add client_email to older databases that do not have it yet.
        columns = {
            row["name"]
            for row in db.execute("PRAGMA table_info(appointments)")
        }

        if "client_email" not in columns:
            db.execute(
                """
                ALTER TABLE appointments
                ADD COLUMN client_email TEXT NOT NULL
                DEFAULT 'client@solace.com'
                """
            )


init_db()


# ==========================================
# 3. STATIC FILE ROUTES
# ==========================================

# Supports older pages that use href="styles.css".
@app.route("/styles.css")
@app.route("/<path:subpath>/styles.css")
def serve_css(subpath=None):
    return send_from_directory(STATIC_DIR, "styles.css")


@app.route("/sean-pages.js")
def serve_sean_page_scripts():
    js_directory = os.path.join(FRONTEND_DIR, "static", "js")
    return send_from_directory(js_directory, "sean-pages.js")


# ==========================================
# 4. HELPERS
# ==========================================

def display_appointment_date(value):
    try:
        parsed = date.fromisoformat(value)
        return f"{parsed.strftime('%B')} {parsed.day}, {parsed.year}"
    except (TypeError, ValueError):
        return value


def appointment_sort_key(date_value, time_value):
    try:
        parsed = datetime.strptime(
            f"{date_value} {time_value}",
            "%Y-%m-%d %I:%M %p",
        )
        return parsed.timestamp()
    except (TypeError, ValueError):
        return 0


def next_appointment():
    """Return the soonest non-cancelled appointment from today on, or None."""
    with get_db() as db:
        row = db.execute(
            """
            SELECT * FROM appointments
            WHERE status != 'Cancelled' AND date >= ?
            ORDER BY date, time
            LIMIT 1
            """,
            (date.today().isoformat(),),
        ).fetchone()

    if not row:
        return None

    item = dict(row)
    item["display_date"] = display_appointment_date(item["date"])
    return item


# ==========================================
# 5. LANDING AND CLIENT ROUTES
# ==========================================

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/client")
def client_dashboard():
    user = {
        "name": "Binibirocha",
        "display_name": "User, name",
        "role": "Client",
    }

    return render_template(
        "Client-dashboard.html",
        role="client",
        active_tab="dashboard",
        user=user,
        upcoming=next_appointment(),
    )


# ==========================================
# 6. PROFILE DEFAULTS AND HELPERS
# ==========================================

PROFILE_DEFAULTS = {
    "client": {
        "name": "CalmCloud27",
        "email": "Client@example.com",
        "profile_type": "Anonymous Profile",
        "bio": (
            "I enjoy quiet moments, meaningful conversations, and finding "
            "small ways to grow each day. I’m using Solace to make space for "
            "my wellbeing and connect with the right support."
        ),
        "privacy": "Anonymous to other users",
        "timezone": "Asia/Manila",
        "contact_preference": "Email",
    },
    "therapist": {
        "name": "Dr. BBno$",
        "email": "Therapist@example.com",
        "title": "Psychologist",
        "bio": (
            "No introduction added yet. Let clients know a little about "
            "your approach and the support you offer."
        ),
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
        "bio": (
            "Responsible for keeping the Solace community safe, supportive, "
            "and running smoothly."
        ),
        "department": "Trust and Safety",
        "access_level": "Full platform administration",
        "security_status": "Two-step verification enabled",
        "notification_email": True,
        "notification_security": True,
        "notification_reports": True,
    },
}


def saved_profile(role):
    """Return the saved profile combined with its default values."""
    with get_db() as db:
        row = db.execute(
            "SELECT data FROM profiles WHERE role = ?",
            (role,),
        ).fetchone()

    saved_data = json.loads(row["data"]) if row else {}
    return {**PROFILE_DEFAULTS[role], **saved_data}


# ==========================================
# 7. THERAPIST ROUTES
# ==========================================

@app.route("/therapist")
def therapist_home():
    today = date.today()

    calendar_days = []
    for offset in range(-3, 11):
        day = today + timedelta(days=offset)
        calendar_days.append(
            {
                "day": day.strftime("%a"),
                "date": day.day,
                "iso": day.isoformat(),
                "active": offset == 0,
            }
        )

    status_map = {"Confirmed": "Approved", "Pending": "Pending"}

    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM appointments ORDER BY created_at DESC LIMIT 3"
        ).fetchall()

    notifications = [
        {
            "id": row["client"],
            "duration": (
                f"{display_appointment_date(row['date'])}, {row['time']}"
            ),
            "status": status_map.get(row["status"], "In Progress"),
        }
        for row in rows
    ]

    user = {
        "name": "Dr. Rizzler",
        "display_name": "Dr. BBno$",
        "role": "Therapist",
    }

    return render_template(
        "Therapist-dashboard.html",
        role="therapist",
        active_tab="dashboard",
        user=user,
        upcoming=next_appointment(),
        calendar_days=calendar_days,
        notifications=notifications,
    )


@app.route("/therapist/bookings")
def therapist_bookings():
    with get_db() as db:
        bookings = [
            dict(row)
            for row in db.execute(
                "SELECT * FROM appointments ORDER BY date, time"
            )
        ]

    for booking in bookings:
        booking["display_date"] = display_appointment_date(
            booking["date"]
        )
        booking["sort_key"] = appointment_sort_key(
            booking["date"],
            booking["time"],
        )

    user = {
        "name": "Dr. BBno$",
        "display_name": "Dr. BBno$",
        "role": "Therapist",
    }

    return render_template(
        "Bookings.html",
        role="therapist",
        active_page="bookings",
        bookings=bookings,
        user=user,
    )


@app.route("/therapist/appointments")
def therapist_appointments():
    with get_db() as db:
        appointments = [
            dict(row)
            for row in db.execute(
                "SELECT * FROM appointments ORDER BY date, time"
            )
        ]

        stats = {
            "upcoming": db.execute(
                """
                SELECT COUNT(*)
                FROM appointments
                WHERE status = 'Confirmed' AND date >= ?
                """,
                (date.today().isoformat(),),
            ).fetchone()[0],
            "pending": db.execute(
                """
                SELECT COUNT(*)
                FROM appointments
                WHERE status = 'Pending'
                """
            ).fetchone()[0],
            "active_users": db.execute(
                """
                SELECT COUNT(DISTINCT client)
                FROM appointments
                WHERE status != 'Cancelled'
                """
            ).fetchone()[0],
            "next_session": next(
                (
                    row["time"]
                    for row in appointments
                    if row["status"] == "Confirmed"
                    and row["date"] >= date.today().isoformat()
                ),
                "—",
            ),
        }

    for appointment in appointments:
        appointment["display_date"] = display_appointment_date(
            appointment["date"]
        )
        appointment["sort_key"] = appointment_sort_key(
            appointment["date"],
            appointment["time"],
        )

    user = {
        "name": "Dr. BBno$",
        "display_name": "Dr. BBno$",
        "role": "Therapist",
    }

    return render_template(
        "Appointments.html",
        role="therapist",
        active_page="appointments",
        appointments=appointments,
        stats=stats,
        user=user,
    )


# ==========================================
# 8. PROFILE AND SETTINGS ROUTES
# ==========================================

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
        "client": "User-profile.html",
        "therapist": "Therapist-profile.html",
        "admin": "Admin-profile.html",
    }

    return render_template(
        templates[role],
        role=role,
        active_page="profile",
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
        profile=profile,
        user=user,
    )


@app.route("/api/profile/<role>", methods=["PUT"])
def update_profile(role):
    if role not in PROFILE_DEFAULTS:
        return jsonify(error="Unknown profile role."), 404

    payload = request.get_json(silent=True) or {}
    profile = saved_profile(role)

    # Only allow fields defined in the defaults for this role.
    profile.update(
        {
            key: value
            for key, value in payload.items()
            if key in PROFILE_DEFAULTS[role]
        }
    )

    with get_db() as db:
        db.execute(
            """
            INSERT INTO profiles (role, data)
            VALUES (?, ?)
            ON CONFLICT(role)
            DO UPDATE SET data = excluded.data
            """,
            (role, json.dumps(profile)),
        )

    return jsonify(profile)


# ==========================================
# 9. APPOINTMENT API ROUTES
# ==========================================

@app.route("/api/appointments", methods=["POST"])
def create_appointment():
    payload = request.get_json(silent=True) or {}

    required_fields = ("client", "therapist", "date", "time")

    if any(
        not str(payload.get(field, "")).strip()
        for field in required_fields
    ):
        return jsonify(
            error="Client, therapist, date, and time are required."
        ), 400

    with get_db() as db:
        cursor = db.execute(
            """
            INSERT INTO appointments (
                client,
                client_email,
                therapist,
                date,
                time,
                session_type
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(payload["client"]).strip(),
                str(
                    payload.get(
                        "client_email",
                        "client@solace.com",
                    )
                ).strip(),
                str(payload["therapist"]).strip(),
                str(payload["date"]).strip(),
                str(payload["time"]).strip(),
                str(
                    payload.get(
                        "session_type",
                        "Online consultation",
                    )
                ).strip(),
            ),
        )

        created_row = db.execute(
            "SELECT * FROM appointments WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()

        created = dict(created_row)

    return jsonify(created), 201


@app.route("/api/appointments/<int:appointment_id>", methods=["PATCH"])
def update_appointment(appointment_id):
    payload = request.get_json(silent=True) or {}
    status = payload.get("status")

    allowed_statuses = (
        "Pending",
        "Confirmed",
        "Completed",
        "Cancelled",
    )

    if status not in allowed_statuses:
        return jsonify(error="Invalid appointment status."), 400

    with get_db() as db:
        cursor = db.execute(
            """
            UPDATE appointments
            SET status = ?
            WHERE id = ?
            """,
            (status, appointment_id),
        )

        if cursor.rowcount == 0:
            return jsonify(error="Appointment not found."), 404

    return jsonify(
        id=appointment_id,
        status=status,
    )


# ==========================================
# 10. RUN THE APPLICATION
# ==========================================

if __name__ == "__main__":
    app.run(debug=True, port=5000)