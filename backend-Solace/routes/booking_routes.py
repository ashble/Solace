from datetime import datetime
from flask import Blueprint, jsonify, request
from extensions import db
from models import Appointment, TherapistProfile, User
from auth_helpers import current_user, csrf_required, login_required

booking_bp = Blueprint("booking", __name__, url_prefix="/api/bookings")


def serialize(item):
    return {"id": item.id, "client_id": item.client_id, "therapist_id": item.therapist_id,
            "scheduled_at": item.scheduled_at.isoformat(), "duration_minutes": item.duration_minutes,
            "status": item.status, "session_type": item.session_type, "notes": item.notes}


@booking_bp.get("")
@login_required
def list_bookings():
    user = current_user()
    query = Appointment.query
    query = query.filter_by(client_id=user.id) if user.role == "client" else query.filter_by(therapist_id=user.id)
    return jsonify(bookings=[serialize(a) for a in query.order_by(Appointment.scheduled_at.desc()).all()])


@booking_bp.post("")
@csrf_required
@login_required
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
    item = Appointment(client_id=user.id, therapist_id=therapist_id, scheduled_at=scheduled_at,
                       duration_minutes=duration,
                       session_type=str(payload.get("session_type", "online"))[:20],
                       notes=str(payload.get("notes", ""))[:2000])
    db.session.add(item)
    db.session.commit()
    return jsonify(booking=serialize(item)), 201


@booking_bp.patch("/<int:booking_id>/status")
@csrf_required
@login_required
def change_status(booking_id):
    user = current_user()
    item = db.session.get(Appointment, booking_id)
    if not item:
        return jsonify(error="Booking not found."), 404
    if user.id == item.therapist_id:
        allowed = {"confirmed", "cancelled"}
    elif user.id == item.client_id:
        allowed = {"cancelled"}
    else:
        return jsonify(error="You cannot change this booking."), 403
    status = str((request.get_json(silent=True) or {}).get("status", "")).lower()
    if status not in allowed or item.status != "pending":
        return jsonify(error="Invalid booking status transition."), 400
    item.status = status
    db.session.commit()
    return jsonify(booking=serialize(item))
