from flask import Blueprint, render_template, redirect

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/admin")
@admin_bp.route("/admin/dashboard")
def admin_dashboard():
    user = {
        "name": "Solace Administrator",
        "display_name": "User, name",
        "role": "Administrator",
    }
    stats = {
        "total_reports": "12,345",
        "urgent_reports": "123",
        "admins_online": "12",
    }
    pending_verifications = [
        {"name": "Dr. Doofenshmirtz", "date": "October 26, 2026"},
        {"name": "Dr. Eggman", "date": "October 26, 2026"},
        {"name": "Dr. Shaun Murphy", "date": "October 24, 2026"},
    ]
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
    return render_template("admin-user-management.html", users=users, user=user)

@admin_bp.route("/admin/reports")
def admin_reports():
    reports = [
        {"id": "REP-1042", "reporter": "Anonymous Client", "subject": "Therapist late to session", "category": "Conduct", "severity": "Normal", "date": "Oct 27, 2026", "status": "Pending"},
        {"id": "REP-1041", "reporter": "Dr. BBno$", "subject": "Client harassment in chat", "category": "Abuse", "severity": "Urgent", "date": "Oct 26, 2026", "status": "Under Review"},
        {"id": "REP-1040", "reporter": "Anonymous User", "subject": "Billing issue on booking", "category": "Billing", "severity": "Normal", "date": "Oct 25, 2026", "status": "Resolved"},
        {"id": "REP-1039", "reporter": "System Monitor", "subject": "Multiple failed login attempts", "category": "Security", "severity": "Urgent", "date": "Oct 24, 2026", "status": "Pending"}
    ]
    stats = {"total": "12,345", "urgent": "123", "resolved": "11,890"}
    user = {"name": "Solace Administrator", "display_name": "User, name", "role": "Administrator"}
    return render_template("admin-reports.html", reports=reports, stats=stats, user=user)

@admin_bp.route("/admin/therapist-verification")
def admin_therapist_verification():
    verifications = [
        {"id": "VER-401", "name": "Dr. Doofenshmirtz", "license": "PSY-99482-TX", "specialty": "Clinical Psychology", "institution": "Evil Inc University", "date": "October 26, 2026", "status": "Pending", "avatar": "D"},
        {"id": "VER-402", "name": "Dr. Eggman", "license": "MED-77123-CA", "specialty": "Cognitive Behavior", "institution": "Robotnik Institute", "date": "October 26, 2026", "status": "Pending", "avatar": "E"},
        {"id": "VER-403", "name": "Dr. Shaun Murphy", "license": "SUR-10482-CA", "specialty": "Autism & Counseling", "institution": "St. Bonaventure Hospital", "date": "October 24, 2026", "status": "Pending", "avatar": "S"}
    ]
    user = {"name": "Solace Administrator", "display_name": "User, name", "role": "Administrator"}
    return render_template("admin-therapist-verification.html", verifications=verifications, user=user)

@admin_bp.route("/admin/therapist/verify/<int:id>", methods=["POST"])
@admin_bp.route("/admin/therapist/reject/<int:id>", methods=["POST"])
def admin_therapist_action(id):
    return redirect("/admin/therapist-verification")

@admin_bp.route("/admin/reports/resolve/<string:id>", methods=["POST"])
def admin_report_resolve(id):
    return redirect("/admin/reports")