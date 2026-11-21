import os
import json
import secrets
from datetime import date, datetime, timedelta

import click
from auth_helpers import account_display, account_required, csrf_required, csrf_token, current_user, dashboard_url
from database import AccountSchemaUnavailable, get_db, migrate_accounts

from flask import (
    Flask,
    jsonify,
    render_template,
    send_from_directory,
    request,
    session,
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
if os.path.isdir(os.path.join(FRONTEND_DIR, "static")):
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

production = os.environ.get("SOLACE_PRODUCTION") == "1"
secret_key = os.environ.get("SECRET_KEY")
if production and (not secret_key or len(secret_key) < 32):
    raise RuntimeError("Production requires a random SECRET_KEY of at least 32 characters.")
app.config.update(
    SECRET_KEY=secret_key or secrets.token_hex(32),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=production,
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
    SESSION_REFRESH_EACH_REQUEST=False,
    MAX_CONTENT_LENGTH=64 * 1024,
    DATABASE=os.environ.get("SOLACE_DATABASE") or os.path.join(CURRENT_DIR, "solace.db"),
)
app.jinja_env.globals.update(csrf_token=csrf_token, current_user=current_user, dashboard_url=dashboard_url)

TIME_SLOTS = ("8:00 AM", "9:00 AM", "10:00 AM", "11:00 AM", "1:00 PM",
              "2:00 PM", "3:00 PM", "4:00 PM", "5:00 PM")


@app.cli.command("migrate-accounts")
def migrate_accounts_command():
    """Apply the additive account migration to the configured SQLite database."""
    migrate_accounts()
    click.echo("Account schema is ready.")


@app.errorhandler(AccountSchemaUnavailable)
def schema_unavailable(error):
    message = "Account setup is unavailable until the database migration is applied."
    if request.path.startswith("/api/"):
        return jsonify(error=message), 503
    return render_template("account-unavailable.html", error=message), 503


@app.after_request
def prevent_account_response_caching(response):
    if "user_id" in session or request.blueprint == "auth" or request.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


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
    return send_from_directory(os.path.join(STATIC_DIR, "css"), "styles.css")

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
        "name": "Client pseudonym",
        "email": "",
        "profile_type": "Anonymous Profile",
        "bio": "",
        "privacy": "Anonymous to other users",
        "timezone": "Asia/Manila",
        "contact_preference": "Email",
    },
    "therapist": {
        "name": "Therapist profile",
        "email": "",
        "title": "Therapist",
        "bio": "",
        "education": "Not provided yet",
        "specialty": "Not provided yet",
        "certifications": "Not provided yet",
        "availability": "Not provided yet",
        "license": "",
        "session_format": "Online and in person",
    },
    "admin": {
        "name": "Administrator profile",
        "email": "",
        "title": "System Administrator",
        "bio": "",
        "department": "Not configured",
        "access_level": "Not configured",
        "security_status": "Not configured",
        "notification_email": True,
        "notification_security": True,
        "notification_reports": True,
    },
}


def saved_profile(account, db=None):
    if db is None:
        with get_db() as connection:
            return saved_profile(account, connection)
    row = db.execute("SELECT data FROM account_profiles WHERE user_id = ?", (account["id"],)).fetchone()
    data = json.loads(row["data"]) if row else {}
    return {
        **PROFILE_DEFAULTS[account["role"]],
        "name": account["name"],
        **data,
        "email": account["email"],
    }


@app.route("/profile")
@account_required()
def profile_page():
    account = current_user()
    role = account["role"]
    profile = saved_profile(account)
    template = {"client": "user-profile.html", "therapist": "therapist-profile.html", "admin": "admin-profile.html"}
    return render_template(
        template[role], role=role, active_page="profile", active_tab="profile",
        profile=profile, user=account_display(account, profile["name"]),
    )


@app.route("/settings")
@account_required()
def settings_page():
    account = current_user()
    profile = saved_profile(account)
    return render_template(
        "index.html", role=account["role"], active_tab="settings", active_page="settings",
        profile=profile, user=account_display(account, profile["name"]),
    )


@app.route("/api/profile/<role>", methods=["PUT"])
@account_required()
@csrf_required
def update_profile(role):
    account = current_user()
    if role != account["role"]:
        return jsonify(error="You can only edit your own profile."), 403
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error="Expected a profile object."), 400
    locked = {"email", "access_level", "security_status", "license"}
    editable = set(PROFILE_DEFAULTS[role]) - locked
    if payload.keys() - editable:
        return jsonify(error="One or more profile fields cannot be edited."), 400
    for key, value in payload.items():
        if isinstance(PROFILE_DEFAULTS[role][key], bool):
            if not isinstance(value, bool):
                return jsonify(error="Notification preferences must be true or false."), 400
        elif not isinstance(value, str) or len(value) > (2000 if key == "bio" else 120):
            return jsonify(error="A profile field exceeds its allowed length or format."), 400
    if "name" in payload and not payload["name"].strip():
        return jsonify(error="Display name is required."), 400
    with get_db() as db:
        db.execute("BEGIN IMMEDIATE")
        profile = saved_profile(account, db)
        profile.update(payload)
        db.execute(
            """INSERT INTO account_profiles (user_id, data) VALUES (?, ?)
               ON CONFLICT(user_id) DO UPDATE SET data = excluded.data""",
            (account["id"], json.dumps({key: profile[key] for key in editable})),
        )
    return jsonify(profile)


@app.route("/api/appointments", methods=["POST"])
@account_required("client")
@csrf_required
def create_appointment():
    account = current_user()
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error="Expected an appointment request object."), 400
    try:
        therapist_id = payload["therapist_id"]
        if type(therapist_id) is not int or not 0 < therapist_id < 2**63:
            raise ValueError
        appointment_date = date.fromisoformat(payload["date"])
        time = payload["time"]
        if time not in TIME_SLOTS:
            raise ValueError
        starts_at = datetime.combine(appointment_date, datetime.strptime(time, "%I:%M %p").time())
        if starts_at <= datetime.now():
            raise ValueError
    except (KeyError, TypeError, ValueError):
        return jsonify(error="Choose an available therapist, future date, and time slot."), 400

    with get_db() as db:
        db.execute("BEGIN IMMEDIATE")
        therapist = db.execute(
            "SELECT id, name FROM users WHERE id = ? AND role = 'therapist' AND status = 'active'",
            (therapist_id,),
        ).fetchone()
        if therapist is None:
            return jsonify(error="Therapist is unavailable."), 404
        if db.execute(
            """SELECT 1 FROM appointments WHERE therapist_id = ? AND date = ? AND time = ?
               AND (status = 'Confirmed' OR (client_id = ? AND status = 'Pending'))""",
            (therapist_id, appointment_date.isoformat(), time, account["id"]),
        ).fetchone():
            return jsonify(error="That appointment was already requested or the slot is booked."), 409
        appointment = db.execute(
            """INSERT INTO appointments (client, client_email, therapist, date, time, client_id, therapist_id)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (saved_profile(account, db)["name"], account["email"], therapist["name"],
             appointment_date.isoformat(), time, account["id"], therapist_id),
        )
        appointment_id = appointment.lastrowid
    return jsonify(id=appointment_id, status="Pending"), 201


@app.route("/api/appointments/<int:appointment_id>", methods=["PATCH"])
@account_required("therapist")
@csrf_required
def update_appointment(appointment_id):
    payload = request.get_json(silent=True)
    status = payload.get("status") if isinstance(payload, dict) else None
    if status not in ("Confirmed", "Completed", "Cancelled"):
        return jsonify(error="Invalid appointment status."), 400
    if not 0 < appointment_id < 2**63:
        return jsonify(error="Appointment not found."), 404
    therapist_id = current_user()["id"]
    with get_db() as db:
        db.execute("BEGIN IMMEDIATE")
        appointment = db.execute(
            """SELECT status, date, time FROM appointments
               WHERE id = ? AND therapist_id = ? AND client_id IS NOT NULL""",
            (appointment_id, therapist_id),
        ).fetchone()
        if appointment is None:
            return jsonify(error="Appointment not found."), 404
        allowed = {"Pending": ("Confirmed", "Cancelled"), "Confirmed": ("Completed", "Cancelled")}
        if status not in allowed.get(appointment["status"], ()):
            return jsonify(error="Invalid appointment status transition."), 409
        if status == "Confirmed" and db.execute(
            """SELECT 1 FROM appointments WHERE therapist_id = ? AND date = ? AND time = ?
               AND status = 'Confirmed' AND client_id IS NOT NULL""",
            (therapist_id, appointment["date"], appointment["time"]),
        ).fetchone():
            return jsonify(error="The therapist already confirmed an appointment at that time."), 409
        db.execute("UPDATE appointments SET status = ? WHERE id = ?", (status, appointment_id))
    return jsonify(id=appointment_id, status=status)


# ==========================================
# 6. REGISTER MODULAR BLUEPRINTS
# ==========================================

from routes.client_routes import client_bp
from routes.admin_routes import admin_bp
from routes.therapist_routes import therapist_bp
from routes.auth_routes import auth_bp, provision_admin

app.register_blueprint(client_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(therapist_bp)
app.register_blueprint(auth_bp)
app.cli.add_command(provision_admin)

# ==========================================
# 7. RUN SERVER
# ==========================================

if __name__ == "__main__":
    app.run(port=5000)
