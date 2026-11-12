import os
import uuid

from flask import Blueprint, current_app, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename

from extensions import db
from models import Report, ReportAttachment

report_bp = Blueprint("reports", __name__)
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "pdf"}
MAX_REPORT_FILE_BYTES = 10 * 1024 * 1024


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@report_bp.post("/api/reports")
def create_report():
    form = request.form
    concern = form.get("concern", "").strip()
    description = form.get("description", "").strip()
    anonymous = form.get("anonymous", "false").lower() in {"true", "1", "yes", "on"}
    reporter_identifier = form.get("reporter_identifier", "").strip()
    reporter_role = form.get("reporter_role", "").strip().lower()
    reported_identifier = form.get("reported_user_identifier", "").strip()

    if not concern or not description or not reported_identifier:
        return jsonify(error="Concern, description, and reported user are required."), 400
    if len(concern) > 120 or len(reporter_identifier) > 120 or len(reported_identifier) > 120:
        return jsonify(error="Concern and user identifiers must be 120 characters or fewer."), 400
    if not anonymous and not reporter_identifier:
        return jsonify(error="Enter your username or user number, or choose anonymous."), 400
    if reporter_role and reporter_role not in {"client", "therapist"}:
        return jsonify(error="Reporter role must be client or therapist."), 400

    files = [uploaded for uploaded in request.files.getlist("files") if uploaded and uploaded.filename]
    for uploaded in files:
        if not allowed_file(uploaded.filename):
            return jsonify(error="Attachments must be PNG, JPG, WEBP, or PDF files."), 400
        uploaded.stream.seek(0, os.SEEK_END)
        size = uploaded.stream.tell()
        uploaded.stream.seek(0)
        if size > MAX_REPORT_FILE_BYTES:
            return jsonify(error="Each attachment must be 10 MB or smaller."), 400

    upload_dir = current_app.config["REPORT_UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)
    report = Report(
        reporter_identifier=None if anonymous else reporter_identifier,
        reporter_role=None if anonymous else (reporter_role or None),
        reporter_is_anonymous=anonymous,
        reported_user_identifier=reported_identifier,
        concern_type=concern,
        description=description,
    )
    saved_paths = []
    try:
        db.session.add(report)
        db.session.flush()
        for uploaded in files:
            original = secure_filename(uploaded.filename) or "attachment"
            extension = original.rsplit(".", 1)[1].lower()
            stored = f"{uuid.uuid4().hex}.{extension}"
            destination = os.path.join(upload_dir, stored)
            uploaded.save(destination)
            saved_paths.append(destination)
            db.session.add(ReportAttachment(
                report_id=report.id,
                original_filename=original,
                storage_name=stored,
                content_type=uploaded.mimetype,
            ))
        db.session.commit()
    except Exception:
        db.session.rollback()
        for saved_path in saved_paths:
            if os.path.exists(saved_path):
                os.remove(saved_path)
        raise

    return jsonify(id=report.id, log_id=report.log_id, status=report.status), 201


@report_bp.get("/admin/reports/<int:report_id>/attachments/<int:attachment_id>")
def download_report_attachment(report_id, attachment_id):
    attachment = ReportAttachment.query.filter_by(id=attachment_id, report_id=report_id).first_or_404()
    return send_from_directory(
        current_app.config["REPORT_UPLOAD_FOLDER"],
        attachment.storage_name,
        as_attachment=True,
        download_name=attachment.original_filename,
    )
