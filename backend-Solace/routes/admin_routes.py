from datetime import datetime
from flask import Blueprint, render_template, redirect, jsonify, request, abort
from extensions import db
from models import Report, TherapistVerification

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/admin")
@admin_bp.route("/admin/dashboard")
def admin_dashboard():
    user = {
        "name": "Solace Administrator",
        "display_name": "User, name",
        "role": "Administrator",
    }
    all_reports = Report.query.order_by(Report.created_at.desc()).all()
    stats = {
        "total_reports": len(all_reports),
        "urgent_reports": sum(1 for report in all_reports if (report.severity or "").lower() == "urgent"),
        "admins_online": "—",
    }
    pending_verifications = [
    {
        "name": item.user.name if item.user else "Unknown therapist",
        "date": item.submitted_at.strftime("%B %d, %Y")
        if item.submitted_at else "",
    }
    for item in TherapistVerification.query.filter(
        TherapistVerification.status.in_(["pending", "Pending"])
    ).order_by(TherapistVerification.submitted_at.desc()).all()     
    ]
    recent_reports = [
        {
            "name": f"{report.concern_type} — {report.reported_user_label}",
            "date": report.created_at.strftime("%B %d, %Y") if report.created_at else "",
        }
        for report in all_reports[:3]
    ]
    return render_template(
        "admin-dashboard.html",
        role="admin",
        active_tab="dashboard",
        active_page="dashboard",
        user=user,
        stats=stats,
        pending_verifications=pending_verifications,
        recent_reports=recent_reports,
    )

@admin_bp.route("/admin/user-management")
def admin_user_management():
    users = [
        {"name": "Skibidi Ohio", "email": "skibidi.ohio@solace.internal", "role": "Client", "status": "Active"},
        {"name": "Dr. Sigma Male", "email": "sigma.male@solace.internal", "role": "Therapist", "status": "Active"},
        {"name": "Admin Gyatt", "email": "admin.gyatt@solace.internal", "role": "Administrator", "status": "Active"},
        {"name": "Rizzler Jenkins", "email": "rizzler.j@solace.internal", "role": "Client", "status": "Suspended"},
        {"name": "Dr. Livvy Dunne", "email": "livvy.d@solace.internal", "role": "Therapist", "status": "Active"}
    ]
    user = {"name": "Solace Administrator", "display_name": "User, name", "role": "Administrator"}
    return render_template("admin-user-management.html", users=users, user=user, active_page="users")

@admin_bp.route("/admin/reports")
def admin_reports():
    reports = Report.query.order_by(Report.created_at.desc()).all()
    total = len(reports)
    urgent = sum(1 for report in reports if (report.severity or "").lower() == "urgent")
    resolved = sum(1 for report in reports if (report.status or "").lower() == "resolved")
    stats = {"total": total, "urgent": urgent, "resolved": resolved}
    user = {"name": "Solace Administrator", "display_name": "User, name", "role": "Administrator"}
    return render_template("admin-reports.html", reports=reports, stats=stats, user=user, active_page="reports")

@admin_bp.post("/admin/reports/<int:report_id>/status")
def admin_report_update_status(report_id):
    report = db.session.get(Report, report_id)
    if report is None:
        abort(404)
    payload = request.get_json(silent=True) or {}
    status = str(payload.get("status", "")).strip().lower()
    if status not in {"pending", "resolved"}:
        return jsonify(error="Status must be Pending or Resolved."), 400
    report.status = status
    report.resolved_at = datetime.utcnow() if status == "resolved" else None
    db.session.commit()
    return jsonify(id=report.id, status=report.status, resolved_at=report.resolved_at.isoformat() if report.resolved_at else None)

@admin_bp.route("/admin/therapist-verification")
def admin_therapist_verification():
    verifications = [
        {"id": "VER-401", "name": "Dr. Doofenshmirtz", "license": "PSY-99482-TX", "specialty": "Clinical Psychology", "institution": "Evil Inc University", "date": "October 26, 2026", "status": "Pending", "avatar": "D"},
        {"id": "VER-402", "name": "Dr. Eggman", "license": "MED-77123-CA", "specialty": "Cognitive Behavior", "institution": "Robotnik Institute", "date": "October 26, 2026", "status": "Pending", "avatar": "E"},
        {"id": "VER-403", "name": "Dr. Shaun Murphy", "license": "SUR-10482-CA", "specialty": "Autism & Counseling", "institution": "St. Bonaventure Hospital", "date": "October 24, 2026", "status": "Pending", "avatar": "S"}
    ]
    user = {"name": "Solace Administrator", "display_name": "User, name", "role": "Administrator"}
    return render_template("admin-therapist-verification.html", verifications=verifications, user=user, active_page="verification")

@admin_bp.route("/admin/therapist/verify/<int:id>", methods=["POST"])
@admin_bp.route("/admin/therapist/reject/<int:id>", methods=["POST"])
def admin_therapist_action(id):
    return redirect("/admin/therapist-verification")

