from datetime import date

from flask import Blueprint, redirect, render_template, request, url_for

from auth_helpers import account_display, account_required, current_user
from database import AccountSchemaUnavailable, get_db

client_bp = Blueprint("client", __name__)


def listed_therapists():
    try:
        with get_db() as db:
            return db.execute(
                "SELECT id, name FROM users WHERE role = 'therapist' AND status = 'active' ORDER BY name, id"
            ).fetchall()
    except AccountSchemaUnavailable:
        return []


@client_bp.get("/")
def landing_page():
    return render_template("starter.html")


@client_bp.get("/client")
@account_required("client")
def client_dashboard():
    from app import saved_profile

    account = current_user()
    profile = saved_profile(account)
    return render_template(
        "index.html", role="client", active_tab="dashboard", active_page="dashboard",
        user=account_display(account, profile["name"]),
    )


@client_bp.get("/search-therapist")
def search_therapist():
    account = current_user()
    if account is not None and account["status"] != "active":
        account = None
    return render_template(
        "search-therapist.html", therapists=listed_therapists(),
        role=account["role"] if account else None, active_tab="search",
        user=account_display(account) if account else None,
    )


@client_bp.get("/schedule")
@account_required("client")
def client_schedule():
    from app import TIME_SLOTS, display_appointment_date, saved_profile

    account = current_user()
    with get_db() as db:
        appointments = [
            dict(row, display_date=display_appointment_date(row["date"]))
            for row in db.execute(
                """SELECT therapist, date, time, status FROM appointments
                   WHERE client_id = ? AND therapist_id IS NOT NULL ORDER BY date DESC, id DESC""",
                (account["id"],),
            )
        ]
    return render_template(
        "schedule.html", role="client", active_tab="schedule",
        user=account_display(account, saved_profile(account)["name"]),
        therapists=listed_therapists(), preferred_therapist=request.args.get("therapist", type=int),
        time_slots=TIME_SLOTS, earliest_date=date.today().isoformat(), appointments=appointments,
    )


@client_bp.get("/chats")
@account_required("client")
def client_chats():
    return redirect(url_for("client.client_dashboard"))
