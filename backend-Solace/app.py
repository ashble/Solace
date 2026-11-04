import os
import json
import sqlite3
from contextlib import contextmanager
from datetime import date
from flask import Flask, jsonify, render_template, send_from_directory, request, redirect

# ==========================================
# 1. DIRECTORY SETUP & APP CONFIG
# ==========================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "frontend-Solace"))

# Auto-detect templates directory with local fallback
if os.path.exists(os.path.join(FRONTEND_DIR, "templates")):
    TEMPLATES_DIR = os.path.join(FRONTEND_DIR, "templates")
else:
    TEMPLATES_DIR = os.path.join(CURRENT_DIR, "templates")

# Auto-detect static/CSS directory
if os.path.exists(os.path.join(FRONTEND_DIR, "static", "css", "styles.css")):
    STATIC_DIR = os.path.join(FRONTEND_DIR, "static", "css")
elif os.path.exists(os.path.join(FRONTEND_DIR, "static", "styles.css")):
    STATIC_DIR = os.path.join(FRONTEND_DIR, "static")
elif os.path.exists(os.path.join(CURRENT_DIR, "static")):
    STATIC_DIR = os.path.join(CURRENT_DIR, "static")
else:
    STATIC_DIR = CURRENT_DIR

app = Flask(
    __name__,
    template_folder=TEMPLATES_DIR,
    static_folder=STATIC_DIR,
    static_url_path="/static"
)
app.config["SECRET_KEY"] = "solace-secret-key-6767"

DATABASE = os.path.join(CURRENT_DIR, "solace.db")

@contextmanager
def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    with get_db() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT NOT NULL,
            therapist TEXT NOT NULL, client_email TEXT NOT NULL DEFAULT 'client@solace.com', date TEXT NOT NULL, time TEXT NOT NULL,
            session_type TEXT NOT NULL DEFAULT 'Online consultation',
            status TEXT NOT NULL DEFAULT 'Pending', notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
        db.execute("""CREATE TABLE IF NOT EXISTS profiles (
            role TEXT PRIMARY KEY, data TEXT NOT NULL)""")
        columns = {row["name"] for row in db.execute("PRAGMA table_info(appointments)")}
        if "client_email" not in columns:
            db.execute("ALTER TABLE appointments ADD COLUMN client_email TEXT NOT NULL DEFAULT 'client@solace.com'")
        if not db.execute("SELECT 1 FROM appointments LIMIT 1").fetchone():
            sample_rows = [
                ("Anonymous User #6767", "client6767@example.com", "2026-11-06", "9:00 AM", "Confirmed"),
                ("Anonymous User #854", "client854@example.com", "2026-11-06", "10:30 AM", "Cancelled"),
                ("Anonymous User #1234", "client1234@example.com", "2026-11-07", "2:00 PM", "Confirmed"),
                ("Anonymous User #2468", "client2468@example.com", "2026-11-08", "11:00 AM", "Confirmed"),
                ("Anonymous User #5167", "client5167@example.com", "2026-11-09", "1:30 PM", "Pending"),
                ("Anonymous User #3247", "client3247@example.com", "2026-11-10", "3:00 PM", "Confirmed"),
                ("Anonymous User #2048", "client2048@example.com", "2026-11-11", "9:30 AM", "Pending"),
                ("Anonymous User #9876", "client9876@example.com", "2026-11-12", "4:00 PM", "Pending"),
            ]
            db.executemany("INSERT INTO appointments (client, client_email, therapist, date, time, status) VALUES (?, ?, 'Dr. Rizzler6767', ?, ?, ?)", sample_rows)

init_db()

# Serves styles.css whenever href="styles.css" is called
@app.route("/styles.css")
@app.route("/<path:subpath>/styles.css")
def serve_css(subpath=None):
    return send_from_directory(STATIC_DIR, "styles.css")


# ==========================================
# 2. CLIENT ROUTES
# ==========================================
@app.route("/")
@app.route("/client")
def client_dashboard():
    user = {"name": "Binibirocha", "display_name": "User, name", "role": "Client"}
    return render_template("index.html", role="client", active_tab="dashboard", user=user)
