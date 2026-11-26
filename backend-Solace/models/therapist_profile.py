from datetime import datetime
from extensions import db


class TherapistProfile(db.Model):
    """Public-facing therapist details used in therapist search."""
    __tablename__ = "therapist_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    bio = db.Column(db.Text, nullable=True)
    specialties = db.Column(db.Text, nullable=True)  # Comma-separated until a specialty table is needed.
    languages = db.Column(db.Text, nullable=True)
    practice_name = db.Column(db.String(160), nullable=True)
    location = db.Column(db.String(160), nullable=True)
    contact_phone = db.Column(db.String(40), nullable=True)
    session_fee = db.Column(db.Numeric(10, 2), nullable=True)
    is_listed = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

