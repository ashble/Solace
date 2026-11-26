from datetime import datetime
from extensions import db

class TherapistVerification(db.Model):
    __tablename__ = 'therapist_verifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    license_number = db.Column(db.String(80), nullable=False)
    specialization = db.Column(db.String(120), nullable=False)
    experience_years = db.Column(db.Integer, default=1)
    license_document_url = db.Column(db.String(255), nullable=True) # PDF / image link
    status = db.Column(db.String(20), default='pending') # 'pending', 'approved', 'rejected'
    rejection_reason = db.Column(db.Text, nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)