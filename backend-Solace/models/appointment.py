from datetime import datetime
from extensions import db


class Appointment(db.Model):
    """A client booking with a therapist."""
    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    therapist_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    scheduled_at = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False, default=50)
    status = db.Column(db.String(20), nullable=False, default="pending")
    session_type = db.Column(db.String(20), nullable=False, default="online")
    meeting_link = db.Column(db.String(500), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    client = db.relationship(
        "User", foreign_keys=[client_id], backref=db.backref("client_appointments", lazy=True)
    )
    therapist = db.relationship(
        "User", foreign_keys=[therapist_id], backref=db.backref("therapist_appointments", lazy=True)
    )