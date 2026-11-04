from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from datetime import datetime
from app import db
from models.user import User
from models.therapist import TherapistVerification
from models.report import Report

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# 1. Admin Dashboard (Stats + Quick previews)
@admin_bp.route('/')
@admin_bp.route('/dashboard')
def dashboard():
    stats = {
        "total_reports": Report.query.count(),
        "urgent_reports": Report.query.filter_by(severity='urgent', status='pending').count(),
        "admins_online": User.query.filter_by(role='admin', status='active').count()
    }
    pending_verifications = TherapistVerification.query.filter_by(status='pending').order_by(TherapistVerification.submitted_at.desc()).limit(5).all()
    recent_reports = Report.query.order_by(Report.created_at.desc()).limit(5).all()
    
    return render_template(
        'index.html',
        role='admin',
        active_tab='dashboard',
        stats=stats,
        pending_verifications=pending_verifications,
        recent_reports=recent_reports
    )

# 2. Therapist Verification (List & Floating Modal Actions)
@admin_bp.route('/therapist-verification')
def therapist_verification():
    applications = TherapistVerification.query.order_by(TherapistVerification.submitted_at.desc()).all()
    return render_template('admin-therapist-verification.html', applications=applications)

@admin_bp.route('/therapist-verification/<int:app_id>/approve', methods=['POST'])
def approve_therapist(app_id):
    verification = TherapistVerification.query.get_or_404(app_id)
    verification.status = 'approved'
    verification.reviewed_at = datetime.utcnow()
    # Activate user account
    verification.user.status = 'active'
    db.session.commit()
    return redirect(url_for('admin.therapist_verification'))

@admin_bp.route('/therapist-verification/<int:app_id>/reject', methods=['POST'])
def reject_therapist(app_id):
    verification = TherapistVerification.query.get_or_404(app_id)
    verification.status = 'rejected'
    verification.rejection_reason = request.form.get('reason', 'Credentials could not be verified')
    verification.reviewed_at = datetime.utcnow()
    db.session.commit()
    return redirect(url_for('admin.therapist_verification'))

# 3. User Management (Filtering, Role Stats, Actions)
@admin_bp.route('/user-management')
def user_management():
    role_filter = request.args.get('role')
    status_filter = request.args.get('status')
    search_query = request.args.get('search')

    query = User.query
    if role_filter and role_filter != 'All Roles':
        query = query.filter(User.role == role_filter.lower())
    if status_filter and status_filter != 'All Statuses':
        query = query.filter(User.status == status_filter.lower())
    if search_query:
        query = query.filter(User.name.ilike(f"%{search_query}%") | User.email.ilike(f"%{search_query}%"))

    users = query.all()
    stats = {
        "clients": User.query.filter_by(role='client').count(),
        "therapists": User.query.filter_by(role='therapist').count(),
        "admins": User.query.filter_by(role='admin').count()
    }
    return render_template('admin-user-management.html', users=users, stats=stats)

@admin_bp.route('/user-management/<int:user_id>/status', methods=['POST'])
def update_user_status(user_id):
    user = User.query.get_or_404(user_id)
    new_status = request.form.get('status') # 'active', 'suspended', 'flagged'
    if new_status:
        user.status = new_status
        db.session.commit()
    return redirect(url_for('admin.user_management'))

# 4. Reports (Filtering, Status update)
@admin_bp.route('/reports')
def reports():
    status_filter = request.args.get('status')
    concern_filter = request.args.get('concern')
    search_query = request.args.get('search')

    query = Report.query
    if status_filter and status_filter != 'All Statuses':
        query = query.filter(Report.status == status_filter.lower())
    if concern_filter and concern_filter != 'All Concerns':
        query = query.filter(Report.concern_type == concern_filter)
    if search_query:
        query = query.filter(Report.description.ilike(f"%{search_query}%"))

    all_reports = query.order_by(Report.created_at.desc()).all()
    return render_template('admin-reports.html', reports=all_reports)

@admin_bp.route('/reports/<int:report_id>/resolve', methods=['POST'])
def resolve_report(report_id):
    report = Report.query.get_or_404(report_id)
    report.status = 'accomplished'
    report.resolved_at = datetime.utcnow()
    db.session.commit()
    return redirect(url_for('admin.reports'))