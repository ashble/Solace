import re
import secrets
import sqlite3

import click
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask.cli import with_appcontext
from werkzeug.security import check_password_hash, generate_password_hash

from auth_helpers import DASHBOARDS, csrf_required
from database import AccountSchemaUnavailable, get_db

auth_bp = Blueprint("auth", __name__)
EMAIL = re.compile(r"[A-Za-z0-9.!#$%&'*+/=?^`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")
DUMMY_HASH = generate_password_hash(secrets.token_urlsafe(32))


def validate_account(name, email, password):
    if not name or len(name) > 120:
        return "Enter a display name of up to 120 characters."
    if len(email) > 120 or not EMAIL.fullmatch(email):
        return "Enter a valid email address."
    local, domain = email.split("@", 1)
    if (len(local) > 64 or local.startswith(".") or local.endswith(".") or ".." in local
            or any(label.startswith("-") or label.endswith("-") or len(label) > 63
                   for label in domain.split("."))):
        return "Enter a valid email address."
    if not 12 <= len(password) <= 128:
        return "Use a password between 12 and 128 characters."
    return None


def create_account(name, email, password, role, status):
    password_hash = generate_password_hash(password)
    with get_db() as db:
        return db.execute(
            """INSERT INTO users (name, email, password_hash, role, status)
               VALUES (?, ?, ?, ?, ?) ON CONFLICT(email) DO NOTHING""",
            (name, email, password_hash, role, status),
        ).rowcount == 1


@auth_bp.route("/login", methods=["GET", "POST"])
@csrf_required
def login():
    if request.method == "GET":
        return render_template("login.html")
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    with get_db() as db:
        account = db.execute(
            "SELECT id, password_hash, role, status FROM users WHERE email = ?", (email,)
        ).fetchone()
    password_hash = account["password_hash"] if account else DUMMY_HASH
    if not 1 <= len(password) <= 128 or not check_password_hash(password_hash, password) or account is None:
        return render_template("login.html", error="Email or password is incorrect.", email=email), 401
    if account["status"] != "active":
        message = "Your account is awaiting verification." if account["status"] == "pending" else "This account cannot sign in."
        return render_template("login.html", error=message, email=email), 403
    session.clear()
    session["user_id"] = account["id"]
    session.permanent = True
    return redirect(url_for(DASHBOARDS[account["role"]]), code=303)


@auth_bp.route("/register", methods=["GET", "POST"])
@csrf_required
def register():
    if request.method == "GET":
        return render_template("register.html")
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    role = request.form.get("role", "")
    password = request.form.get("password", "")
    values = {"name": name, "email": email, "role": role}
    error = validate_account(name, email, password)
    if role not in {"client", "therapist"}:
        error = "Choose Client or Therapist."
    elif not error and password != request.form.get("confirm"):
        error = "Passwords do not match."
    if error:
        return render_template("register.html", error=error, **values), 400

    status = "pending" if role == "therapist" else "active"
    if not create_account(name, email, password, role, status):
        return render_template("register.html", error="An account with that email already exists.", **values), 409
    flash("Account created. Therapist access is pending verification." if status == "pending"
          else "Account created. You can now sign in.")
    return redirect(url_for("auth.login"), code=303)


@auth_bp.post("/logout")
@csrf_required
def logout():
    session.clear()
    return redirect(url_for("client.landing_page"), code=303)


@click.command("create-admin")
@click.option("--name", prompt="Display name")
@click.option("--email", prompt=True)
@click.password_option()
@with_appcontext
def provision_admin(name, email, password):
    """Provision an administrator from the local Flask CLI."""
    name, email = name.strip(), email.strip().lower()
    error = validate_account(name, email, password)
    if error:
        raise click.ClickException(error)
    try:
        created = create_account(name, email, password, "admin", "active")
    except AccountSchemaUnavailable as exc:
        raise click.ClickException("Apply the account migration first.") from exc
    except sqlite3.Error as exc:
        raise click.ClickException("Could not write the account database.") from exc
    if not created:
        raise click.ClickException("An account with that email already exists.")
    click.echo("Administrator created.")
