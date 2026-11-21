from datetime import date, datetime, timedelta

from flask import Blueprint, render_template

from auth_helpers import account_display, account_required, current_user
from database import get_db

therapist_bp = Blueprint("therapist", __name__)


def assigned_appointments(account):
    from app import appointment_sort_key, display_appointment_date

    with get_db() as db:
        return sorted(
            (
                dict(row, display_date=display_appointment_date(row["date"]),
                     sort_key=appointment_sort_key(row["date"], row["time"]))
                for row in db.execute(
                    """SELECT * FROM appointments
                       WHERE therapist_id = ? AND client_id IS NOT NULL""",
                    (account["id"],),
                )
            ),
            key=lambda row: row["sort_key"],
        )


def upcoming_appointments(appointments):
    now = datetime.now().timestamp()
    return [
        row for row in appointments
        if row["status"] == "Confirmed" and row["sort_key"] >= now
    ]


@therapist_bp.get("/therapist")
@account_required("therapist")
def therapist_home():
    from app import saved_profile

    account = current_user()
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week = [week_start + timedelta(days=offset) for offset in range(7)]
    calendar_days = [
        {"day": day.strftime("%a"), "date": day.day, "active": day == today}
        for day in week
    ]
    upcoming = next(iter(upcoming_appointments(assigned_appointments(account))), None)
    return render_template(
        "index.html", role="therapist", active_tab="dashboard",
        user=account_display(account, saved_profile(account)["name"]), calendar_days=calendar_days,
        upcoming=upcoming, upcoming_date=upcoming["display_date"] if upcoming else None,
    )


@therapist_bp.get("/therapist/bookings")
@account_required("therapist")
def therapist_bookings():
    account = current_user()
    return render_template(
        "bookings.html", role="therapist", active_page="bookings",
        bookings=assigned_appointments(account), user=account_display(account),
    )


@therapist_bp.get("/therapist/appointments")
@account_required("therapist")
def therapist_appointments():
    account = current_user()
    appointments = assigned_appointments(account)
    upcoming = upcoming_appointments(appointments)
    stats = {
        "upcoming": len(upcoming),
        "pending": sum(row["status"] == "Pending" for row in appointments),
        "active_users": len({row["client_id"] for row in appointments if row["status"] != "Cancelled"}),
        "next_session": upcoming[0]["time"] if upcoming else "â€”",
    }
    return render_template(
        "appointments.html", role="therapist", active_page="appointments",
        appointments=appointments, stats=stats, user=account_display(account),
    )
