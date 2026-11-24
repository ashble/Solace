from datetime import datetime
from extensions import db


class UserProfile(db.Model):
    __tablename__ = "user_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    data = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = db.relationship("User", backref=db.backref("account_profile", uselist=False, cascade="all, delete-orphan"))
