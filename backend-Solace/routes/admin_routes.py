from flask import Blueprint, abort, render_template

from auth_helpers import account_display, account_required, csrf_required, current_user
from database import get_db

admin_bp = Blueprint("admin", __name__)


@admin_bp.before_request
@account_required("admin")
def require_administrator():
    pass


@admin_bp.route("/admin/dashboard")
@admin_bp.route("/admin")
def admin_dashboard():
    user = account_display(current_user())
    with get_db() as db:
        admin_count = db.execute(
            "SELECT COUNT(*) FROM users WHERE role = 'admin' AND status = 'active'"
        ).fetchone()[0]
        pending_verifications = db.execute(
            """SELECT name, date(created_at) AS date FROM users
               WHERE role = 'therapist' AND status = 'pending' ORDER BY id DESC LIMIT 5"""
        ).fetchall()
    recent_reports = [
        {"name": "Anonymous User#6767", "date": "October 27, 2026"},
        {"name": "Dr. Eggman", "date": "October 26, 2026"},
        {"name": "Anonymous User#854", "date": "October 24, 2026"},
    ]
    return render_template(
        "index.html",
        role="admin",
        active_tab="dashboard",
        active_page="dashboard",
        user=user,
        admin_count=admin_count,
        pending_verifications=pending_verifications,
        recent_reports=recent_reports,
    )

@admin_bp.route("/admin/user-management")
def admin_user_management():
    with get_db() as db:
        users = db.execute("SELECT name, email, role, status FROM users ORDER BY name, id").fetchall()
    return render_template("admin-user-management.html", users=users, user=account_display(current_user()))


@admin_bp.route("/admin/reports")
def admin_reports():
    reports = [
        {"id": "REP-1042", "reporter": "Anonymous Client", "subject": "Therapist late to session", "category": "Conduct", "severity": "Normal", "date": "Oct 27, 2026", "status": "Pending"},
        {"id": "REP-1041", "reporter": "Dr. BBno$", "subject": "Client harassment in chat", "category": "Abuse", "severity": "Urgent", "date": "Oct 26, 2026", "status": "Under Review"},
        {"id": "REP-1040", "reporter": "Anonymous User", "subject": "Billing issue on booking", "category": "Billing", "severity": "Normal", "date": "Oct 25, 2026", "status": "Resolved"},
        {"id": "REP-1039", "reporter": "System Monitor", "subject": "Multiple failed login attempts", "category": "Security", "severity": "Urgent", "date": "Oct 24, 2026", "status": "Pending"}
    ]
    stats = {"total": "12,345", "urgent": "123", "resolved": "11,890"}
    user = account_display(current_user())
    return render_template("admin-reports.html", reports=reports, stats=stats, user=user)

@admin_bp.route("/admin/therapist-verification")
def admin_therapist_verification():
    with get_db() as db:
        pending = db.execute(
            "SELECT name, email FROM users WHERE role = 'therapist' AND status = 'pending' ORDER BY id"
        ).fetchall()
    return render_template(
        "admin-therapist-verification.html", pending=pending, user=account_display(current_user()),
    )


@admin_bp.route("/admin/therapist/verify/<int:id>", methods=["POST"])
@admin_bp.route("/admin/therapist/reject/<int:id>", methods=["POST"])
@csrf_required
def admin_therapist_action(id):
    abort(501, description="Therapist verification is not available yet.")

@admin_bp.route("/admin/reports/resolve/<string:id>", methods=["POST"])
@csrf_required
def admin_report_resolve(id):
    abort(501, description="Report resolution is not available yet.")