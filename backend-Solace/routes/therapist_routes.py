from datetime import date
from flask import Blueprint, render_template, redirect

therapist_bp = Blueprint("therapist", __name__)

@therapist_bp.route("/therapist")
def therapist_home():
    return redirect("/therapist/appointments")

@therapist_bp.route("/therapist/bookings")
def therapist_bookings():
    # Uses Sean's database logic if available
    from app import get_db, display_appointment_date, appointment_sort_key
    with get_db() as db:
        bookings = [dict(row) for row in db.execute("SELECT * FROM appointments ORDER BY date, time")]

    for b in bookings:
        b["display_date"] = display_appointment_date(b["date"])
        b["sort_key"] = appointment_sort_key(b["date"], b["time"])

    user = {"name": "Dr. BBno$", "display_name": "Dr. BBno$", "role": "Therapist"}
    return render_template("bookings.html", role="therapist", active_page="bookings", bookings=bookings, user=user)

@therapist_bp.route("/therapist/appointments")
def therapist_appointments():
    from app import get_db, display_appointment_date, appointment_sort_key
    with get_db() as db:
        appointments = [dict(row) for row in db.execute("SELECT * FROM appointments ORDER BY date, time")]
        stats = {
            "upcoming": db.execute("SELECT COUNT(*) FROM appointments WHERE status = 'Confirmed' AND date >= ?", (date.today().isoformat(),)).fetchone()[0],
            "pending": db.execute("SELECT COUNT(*) FROM appointments WHERE status = 'Pending'").fetchone()[0],
            "active_users": db.execute("SELECT COUNT(DISTINCT client) FROM appointments WHERE status != 'Cancelled'").fetchone()[0],
            "next_session": next((row["time"] for row in appointments if row["status"] == "Confirmed" and row["date"] >= date.today().isoformat()), "—")
        }

    for a in appointments:
        a["display_date"] = display_appointment_date(a["date"])
        a["sort_key"] = appointment_sort_key(a["date"], a["time"])

    user = {"name": "Dr. BBno$", "display_name": "Dr. BBno$", "role": "Therapist"}
    return render_template("appointments.html", role="therapist", active_page="appointments", appointments=appointments, stats=stats, user=user)
