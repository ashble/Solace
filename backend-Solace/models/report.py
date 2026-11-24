from datetime import datetime
from extensions import db

class Report(db.Model):
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)
    # Nullable until account login is implemented; reporter_identifier is self-reported.
    reporter_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    reporter_identifier = db.Column(db.String(120), nullable=True)
    reporter_role = db.Column(db.String(20), nullable=True)
    reporter_is_anonymous = db.Column(db.Boolean, nullable=False, default=False)
    reported_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    reported_user_identifier = db.Column(db.String(120), nullable=True)
    concern_type = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), nullable=False, default="normal")
    status = db.Column(db.String(20), nullable=False, default="pending")
    admin_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)

    reporter = db.relationship("User", foreign_keys=[reporter_id], backref="reports_submitted")
    reported_user = db.relationship("User", foreign_keys=[reported_user_id], backref="reports_received")
    attachments = db.relationship("ReportAttachment", backref="report", cascade="all, delete-orphan", lazy=True)

    @property
    def log_id(self):
        return f"RPT-{self.id:06d}"

    @property
    def reporter_label(self):
        if self.reporter_is_anonymous:
            return "Anonymous"
        if self.reporter_identifier:
            return self.reporter_identifier
        return self.reporter.name if self.reporter else "Unknown reporter"

    @property
    def reported_user_label(self):
        if self.reported_user_identifier:
            return self.reported_user_identifier
        return self.reported_user.name if self.reported_user else "Unknown user"

class ReportAttachment(db.Model):
    __tablename__ = "report_attachments"

    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    storage_name = db.Column(db.String(255), unique=True, nullable=False)
    content_type = db.Column(db.String(120), nullable=True)
    uploaded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
