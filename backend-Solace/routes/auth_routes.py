import secrets
from flask import Blueprint, jsonify, session
from auth_helpers import current_user

auth_bp = Blueprint("auth", __name__)


@auth_bp.get("/api/csrf")
def csrf_token():
    session.setdefault("csrf_token", secrets.token_urlsafe(32))
    return jsonify(csrf_token=session["csrf_token"])


@auth_bp.get("/api/auth/me")
def me():
    user = current_user()
    if not user:
        return jsonify(user=None), 401
    return jsonify(user={"id": user.id, "name": user.name, "email": user.email, "role": user.role})
