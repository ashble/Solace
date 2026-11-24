from datetime import date
from flask import Blueprint, render_template, redirect
from models import Appointment
from auth_helpers import current_user, role_required

therapist_bp = Blueprint("therapist", __name__)

@therapist_bp.route("/therapist")
@role_required("therapist")
def therapist_home():
    return redirect("/therapist/appointments")

@therapist_bp.route("/therapist/bookings")
@role_required("therapist")
def therapist_bookings():
    from app import display_appointment_date, appointment_sort_key
    user = current_user()
    items = Appointment.query.filter_by(therapist_id=user.id).order_by(Appointment.scheduled_at).all()
    bookings = [appointment_row(item) for item in items]

    for b in bookings:
        b["display_date"] = display_appointment_date(b["date"])
        b["sort_key"] = appointment_sort_key(b["date"], b["time"])

    page_user = {"name": user.name, "display_name": user.name, "role": "Therapist"}
    return render_template("Bookings.html", role="therapist", active_page="bookings", bookings=bookings, user=page_user)

@therapist_bp.route("/therapist/appointments")
@role_required("therapist")
def therapist_appointments():
    from app import display_appointment_date, appointment_sort_key
    user = current_user()
    items = Appointment.query.filter_by(therapist_id=user.id).order_by(Appointment.scheduled_at).all()
    appointments = [appointment_row(item) for item in items]
    stats = {
        "upcoming": sum(1 for item in items if item.status.lower() == "confirmed" and item.date >= date.today().isoformat()),
        "pending": sum(1 for item in items if item.status.lower() == "pending"),
        "active_users": len({item.client_id for item in items if item.client_id and item.status.lower() != "cancelled"}),
        "next_session": next((item.time for item in items if item.status.lower() == "confirmed" and item.date >= date.today().isoformat()), "—"),
    }

    for a in appointments:
        a["display_date"] = display_appointment_date(a["date"])
        a["sort_key"] = appointment_sort_key(a["date"], a["time"])

    page_user = {"name": user.name, "display_name": user.name, "role": "Therapist"}
    return render_template("Appointments.html", role="therapist", active_page="appointments", appointments=appointments, stats=stats, user=page_user)


def appointment_row(item):
    return {"id": item.id, "client": item.client_name, "therapist": item.therapist_name,
            "client_email": item.client_email, "date": item.date, "time": item.time,
            "session_type": item.session_type, "status": item.status, "notes": item.notes or ""}
