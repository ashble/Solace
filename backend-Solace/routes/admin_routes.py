from datetime import datetime
from flask import Blueprint, abort, jsonify, render_template, request
from extensions import db
from models import Report, TherapistVerification, User
from auth_helpers import csrf_required, role_required

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin")
@admin_bp.route("/admin/dashboard")
@role_required("admin")
def admin_dashboard():
    all_reports = Report.query.order_by(Report.created_at.desc()).all()
    stats = {
        "total_reports": len(all_reports),
        "urgent_reports": sum(1 for report in all_reports if (report.severity or "").lower() == "urgent"),
        "admins_online": "—",
    }
    pending_verifications = [
        {"name": item.user.name if item.user else "Unknown therapist",
         "date": item.submitted_at.strftime("%B %d, %Y") if item.submitted_at else ""}
        for item in TherapistVerification.query.filter(TherapistVerification.status.in_(["pending", "Pending"]))
        .order_by(TherapistVerification.submitted_at.desc()).all()
    ]
    recent_reports = [
        {"name": f"{report.concern_type} — {report.reported_user_label}",
         "date": report.created_at.strftime("%B %d, %Y") if report.created_at else ""}
        for report in all_reports[:3]
    ]
    user = {"name": "Solace Administrator", "display_name": "Solace Administrator", "role": "Administrator"}
    return render_template("admin-dashboard.html", role="admin", active_tab="dashboard",
                           active_page="dashboard", user=user, stats=stats,
                           pending_verifications=pending_verifications, recent_reports=recent_reports)


@admin_bp.route("/admin/user-management")
@role_required("admin")
def admin_user_management():
    role_names = {"client": "Client", "therapist": "Therapist", "admin": "Administrator"}
    users = [{"name": item.name, "email": item.email, "role": role_names.get(item.role, item.role.title()),
              "status": item.status.title()}
             for item in User.query.order_by(User.created_at.desc()).all()]
    user = {"name": "Solace Administrator", "display_name": "Solace Administrator", "role": "Administrator"}
    return render_template("admin-user-management.html", users=users, user=user, active_page="users")


@admin_bp.route("/admin/reports")
@role_required("admin")
def admin_reports():
    reports = Report.query.order_by(Report.created_at.desc()).all()
    stats = {
        "total": len(reports),
        "urgent": sum(1 for report in reports if (report.severity or "").lower() == "urgent"),
        "pending": sum(1 for report in reports if (report.status or "").lower() == "pending"),
        "resolved": sum(1 for report in reports if (report.status or "").lower() == "resolved"),
    }
    user = {"name": "Solace Administrator", "display_name": "Solace Administrator", "role": "Administrator"}
    return render_template("admin-reports.html", reports=reports, stats=stats, user=user, active_page="reports")


@admin_bp.patch("/admin/reports/<int:report_id>/status")
@role_required("admin")
@csrf_required
def admin_report_update_status(report_id):
    report = db.session.get(Report, report_id)
    if report is None:
        abort(404)
    payload = request.get_json(silent=True) or {}
    status = str(payload.get("status", "")).strip().lower()
    if status not in {"pending", "resolved"}:
        return jsonify(error="Status must be pending or resolved."), 400
    report.status = status
    report.resolved_at = datetime.utcnow() if status == "resolved" else None
    db.session.commit()
    return jsonify(id=report.id, status=report.status,
                   resolved_at=report.resolved_at.isoformat() if report.resolved_at else None)


@admin_bp.route("/admin/therapist-verification")
@role_required("admin")
def admin_therapist_verification():
    verifications = TherapistVerification.query.order_by(TherapistVerification.submitted_at.desc()).all()
    user = {"name": "Solace Administrator", "display_name": "Solace Administrator", "role": "Administrator"}
    return render_template("admin-therapist-verification.html", verifications=verifications,
                           user=user, active_page="verification")


@admin_bp.route("/admin/therapist/verify/<int:id>", methods=["POST"])
@admin_bp.route("/admin/therapist/reject/<int:id>", methods=["POST"])
@role_required("admin")
@csrf_required
def admin_therapist_action(id):
    verification = db.session.get(TherapistVerification, id)
    if verification is None:
        return jsonify(error="Verification not found."), 404
    if not verification.user:
        return jsonify(error="Verification has no associated user."), 409
    if verification.status.lower() != "pending":
        return jsonify(error="Only pending applications can be reviewed."), 409

    approve = request.path.endswith("/verify/" + str(id))
    payload = request.get_json(silent=True) or {}
    reason = str(payload.get("reason", "")).strip()
    if not approve and not reason:
        return jsonify(error="A rejection reason is required."), 400
    verification.reviewed_at = datetime.utcnow()
    if approve:
        verification.status = "approved"
        verification.rejection_reason = None
        verification.user.status = "active"
        if verification.user.therapist_profile:
            verification.user.therapist_profile.is_listed = True
    else:
        verification.status = "rejected"
        verification.rejection_reason = reason[:2000]
        verification.user.status = "suspended"
        if verification.user.therapist_profile:
            verification.user.therapist_profile.is_listed = False
    db.session.commit()
    return jsonify(id=verification.id, status=verification.status, user_status=verification.user.status)
