from datetime import datetime
from flask import Blueprint, jsonify, request
from extensions import db
from models import Appointment, TherapistProfile, User
from auth_helpers import current_user, csrf_required, role_required

booking_bp = Blueprint("booking", __name__, url_prefix="/api/bookings")
legacy_booking_bp = Blueprint("legacy_booking", __name__)


def serialize(item):
    scheduled_at = item.scheduled_at
    if not scheduled_at:
        try:
            scheduled_at = datetime.strptime(f"{item.date} {item.time}", "%Y-%m-%d %I:%M %p").isoformat()
        except ValueError:
            scheduled_at = None
    return {"id": item.id, "client_id": item.client_id, "therapist_id": item.therapist_id,
            "scheduled_at": scheduled_at, "duration_minutes": item.duration_minutes,
            "status": (item.status or "pending").lower(), "session_type": item.session_type, "notes": item.notes}


@booking_bp.get("")
@role_required("client", "therapist")
def list_bookings():
    user = current_user()
    query = Appointment.query.filter_by(client_id=user.id) if user.role == "client" else Appointment.query.filter_by(therapist_id=user.id)
    return jsonify(bookings=[serialize(a) for a in query.order_by(Appointment.scheduled_at.desc()).all()])


@booking_bp.post("")
@csrf_required
@role_required("client")
def create_booking():
    user = current_user()
    if user.role != "client":
        return jsonify(error="Only clients can book appointments."), 403
    payload = request.get_json(silent=True) or {}
    try:
        therapist_id = int(payload.get("therapist_id"))
        scheduled_at = datetime.fromisoformat(str(payload.get("scheduled_at", "")).replace("Z", "+00:00"))
        duration = int(payload.get("duration_minutes", 50))
    except (TypeError, ValueError):
        return jsonify(error="A therapist_id and ISO 8601 scheduled_at are required."), 400
    if duration < 15 or duration > 240:
        return jsonify(error="Duration must be between 15 and 240 minutes."), 400
    therapist = db.session.get(User, therapist_id)
    if not therapist or therapist.role != "therapist" or therapist.status != "active" or not TherapistProfile.query.filter_by(user_id=therapist_id, is_listed=True).first():
        return jsonify(error="Therapist is unavailable."), 404
    item = Appointment(
        client_id=user.id, therapist_id=therapist.id, client_name=user.name,
        therapist_name=therapist.name, client_email=user.email,
        date=scheduled_at.date().isoformat(), time=scheduled_at.strftime("%I:%M %p").lstrip("0"),
        scheduled_at=scheduled_at.isoformat(), duration_minutes=duration, status="Pending",
        session_type=str(payload.get("session_type", "Online consultation"))[:80],
        notes=str(payload.get("notes", ""))[:2000],
    )
    db.session.add(item)
    db.session.commit()
    return jsonify(booking=serialize(item)), 201


@booking_bp.patch("/<int:booking_id>/status")
@csrf_required
@role_required("client", "therapist")
def change_status(booking_id):
    user = current_user()
    item = db.session.get(Appointment, booking_id)
    if not item:
        return jsonify(error="Booking not found."), 404
    current_status = (item.status or "").lower()
    if user.id == item.therapist_id and user.role == "therapist":
        allowed = {"confirmed", "cancelled"} if current_status == "pending" else ({"completed", "cancelled"} if current_status == "confirmed" else set())
    elif user.id == item.client_id and user.role == "client":
        allowed = {"cancelled"} if current_status in {"pending", "confirmed"} else set()
    else:
        return jsonify(error="You cannot change this booking."), 403
    status = str((request.get_json(silent=True) or {}).get("status", "")).lower()
    if status not in allowed:
        return jsonify(error="Invalid booking status transition."), 400
    item.status = status.title()
    db.session.commit()
    return jsonify(booking=serialize(item))


@legacy_booking_bp.patch("/api/appointments/<int:booking_id>")
@csrf_required
@role_required("client", "therapist")
def update_legacy_booking(booking_id):
    """Compatibility endpoint for older dashboard controls."""
    user = current_user()
    item = db.session.get(Appointment, booking_id)
    if not item:
        return jsonify(error="Appointment not found."), 404
    requested = str((request.get_json(silent=True) or {}).get("status", "")).lower()
    if user.role == "therapist" and item.therapist_id == user.id:
        allowed = {"confirmed", "cancelled"} if item.status.lower() == "pending" else ({"completed", "cancelled"} if item.status.lower() == "confirmed" else set())
    elif user.role == "client" and item.client_id == user.id:
        allowed = {"cancelled"} if item.status.lower() in {"pending", "confirmed"} else set()
    else:
        return jsonify(error="You cannot change this appointment."), 403
    if requested not in allowed:
        return jsonify(error="Invalid appointment status transition."), 400
    item.status = requested.title()
    db.session.commit()
    return jsonify(id=item.id, status=item.status)
