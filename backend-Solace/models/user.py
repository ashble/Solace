from datetime import datetime
from app import db  # or from extensions import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='client') # 'client', 'therapist', 'admin'
    status = db.Column(db.String(20), nullable=False, default='active') # 'active', 'pending', 'suspended', 'flagged'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    therapist_profile = db.relationship('TherapistVerification', backref='user', uselist=False, cascade="all, delete-orphan")
    reports_submitted = db.relationship('Report', foreign_keys='Report.reporter_id', backref='reporter', lazy=True)
    reports_received = db.relationship('Report', foreign_keys='Report.reported_user_id', backref='reported_user', lazy=True)