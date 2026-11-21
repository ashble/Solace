import secrets
from functools import wraps

from flask import abort, g, jsonify, redirect, request, session, url_for

from database import get_db

DASHBOARDS = {
    "client": "client.client_dashboard",
    "therapist": "therapist.therapist_home",
    "admin": "admin.admin_dashboard",
}


def current_user():
    if "account" not in g:
        g.account = None
        if "user_id" in session:
            with get_db() as db:
                g.account = db.execute(
                    "SELECT id, name, email, role, status FROM users WHERE id = ?",
                    (session["user_id"],),
                ).fetchone()
            if g.account is None:
                session.clear()
    return g.account


def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


def csrf_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            expected = session.get("csrf_token")
            token = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token", "")
            if not expected or not secrets.compare_digest(expected.encode(), token.encode()):
                if request.path.startswith("/api/"):
                    return jsonify(error="Invalid or expired form token. Reload this page and try again."), 403
                abort(403, description="Invalid or expired form token. Reload the page and try again.")
        return view(*args, **kwargs)
    return wrapped


def account_required(*roles):
    def decorate(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            account = current_user()
            api = request.path.startswith("/api/")
            if account is None:
                if api:
                    return jsonify(error="Sign in to continue."), 401
                return redirect(url_for("auth.login"))
            if account["status"] != "active" or (roles and account["role"] not in roles):
                if api:
                    return jsonify(error="You do not have access to this action."), 403
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorate


def account_display(account, name=None):
    return {
        "name": name or account["name"],
        "display_name": name or account["name"],
        "role": "Administrator" if account["role"] == "admin" else account["role"].capitalize(),
    }


def dashboard_url():
    account = current_user()
    if account is not None and account["status"] == "active":
        return url_for(DASHBOARDS[account["role"]])
    return url_for("auth.login")
