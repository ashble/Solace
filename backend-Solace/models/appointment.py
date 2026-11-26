from datetime import datetime
from extensions import db


class Appointment(db.Model):
    """Canonical booking rows, retaining display columns for the existing pages."""
    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    therapist_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    # Legacy display fields remain populated so older templates can read the same rows.
    client_name = db.Column("client", db.String(120), nullable=False)
    therapist_name = db.Column("therapist", db.String(120), nullable=False)
    client_email = db.Column(db.String(120), nullable=False, default="client@solace.com")
    date = db.Column(db.String(10), nullable=False)
    time = db.Column(db.String(20), nullable=False)
    scheduled_at = db.Column(db.String(40), nullable=True)
    duration_minutes = db.Column(db.Integer, nullable=False, default=50)
    status = db.Column(db.String(20), nullable=False, default="Pending")
    session_type = db.Column(db.String(80), nullable=False, default="Online consultation")
    meeting_link = db.Column(db.String(500), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    legacy_booking_id = db.Column(db.Integer, nullable=True, unique=True)

    client_user = db.relationship(
        "User", foreign_keys=[client_id], backref=db.backref("client_appointments", lazy=True)
    )
    therapist_user = db.relationship(
        "User", foreign_keys=[therapist_id], backref=db.backref("therapist_appointments", lazy=True)
    )
