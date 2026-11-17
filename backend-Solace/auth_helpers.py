from functools import wraps
from flask import jsonify, session
from models import User


def current_user():
    user_id = session.get("user_id")
    return db_get_user(user_id) if user_id else None


def db_get_user(user_id):
    from extensions import db
    return db.session.get(User, user_id)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user or user.status != "active":
            session.clear()
            return jsonify(error="Authentication required."), 401
        return view(*args, **kwargs)
    return wrapped


def csrf_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        from flask import request
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            token = session.get("csrf_token")
            if not token or request.headers.get("X-CSRF-Token") != token:
                return jsonify(error="Invalid CSRF token."), 403
        return view(*args, **kwargs)
    return wrapped
