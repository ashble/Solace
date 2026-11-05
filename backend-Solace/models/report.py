from datetime import datetime
from app import db

class Report(db.Model):
    __tablename__ = 'reports'

    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reported_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    concern_type = db.Column(db.String(50), nullable=False) # 'Harassment', 'Spam', 'Troll', 'Death Threat'
    description = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), default='normal') # 'urgent', 'normal'
    status = db.Column(db.String(20), default='pending')   # 'pending', 'in_review', 'accomplished'
    admin_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)