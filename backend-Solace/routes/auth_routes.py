import secrets
from flask import Blueprint, jsonify, render_template, session
from auth_helpers import current_user

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login")
def login():
    return render_template("login.html")


@auth_bp.route("/register")
def register():
    return render_template("register.html")


@auth_bp.get("/api/csrf")
def csrf_token():
    session.setdefault("csrf_token", secrets.token_urlsafe(32))
    return jsonify(csrf_token=session["csrf_token"])


@auth_bp.get("/api/auth/me")
def me():
    user = current_user()
    if not user or user.status != "active":
        session.clear()
        return jsonify(user=None), 401
    return jsonify(user={"id": user.id, "name": user.name, "email": user.email, "role": user.role})
