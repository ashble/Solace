import sqlite3
from contextlib import contextmanager
from pathlib import Path

from flask import current_app


class AccountSchemaUnavailable(Exception):
    pass


@contextmanager
def get_db(*, allow_create=False, require_accounts=True):
    path = Path(current_app.config["DATABASE"]).resolve()
    mode = "rwc" if allow_create else "rw"
    if not allow_create and not path.is_file():
        raise AccountSchemaUnavailable
    db = sqlite3.connect(f"{path.as_uri()}?mode={mode}", uri=True)
    db.row_factory = sqlite3.Row
    try:
        db.execute("PRAGMA foreign_keys = ON")
        if require_accounts and db.execute("PRAGMA user_version").fetchone()[0] != 1:
            raise AccountSchemaUnavailable
        with db:
            yield db
    finally:
        db.close()


def migrate_accounts():
    with get_db(allow_create=True, require_accounts=False) as db:
        db.execute("BEGIN IMMEDIATE")
        version = db.execute("PRAGMA user_version").fetchone()[0]
        if version == 1:
            return
        if version != 0:
            raise ValueError(f"Unsupported SQLite schema version {version}.")
        db.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('client', 'therapist', 'admin')),
                status TEXT NOT NULL CHECK (status IN ('active', 'pending', 'suspended', 'flagged')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.execute("""
            CREATE TABLE account_profiles (
                user_id INTEGER PRIMARY KEY REFERENCES users(id),
                data TEXT NOT NULL
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client TEXT NOT NULL,
                therapist TEXT NOT NULL,
                client_email TEXT NOT NULL DEFAULT 'client@solace.com',
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                session_type TEXT NOT NULL DEFAULT 'Online consultation',
                status TEXT NOT NULL DEFAULT 'Pending',
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        columns = {row["name"] for row in db.execute("PRAGMA table_info(appointments)")}
        if "client_email" not in columns:
            db.execute("ALTER TABLE appointments ADD COLUMN client_email TEXT NOT NULL DEFAULT ''")
        # Legacy appointments deliberately retain NULL owners.
        db.execute("ALTER TABLE appointments ADD COLUMN client_id INTEGER REFERENCES users(id)")
        db.execute("ALTER TABLE appointments ADD COLUMN therapist_id INTEGER REFERENCES users(id)")
        db.execute("CREATE INDEX appointments_client ON appointments(client_id, date)")
        db.execute("CREATE INDEX appointments_therapist ON appointments(therapist_id, date)")
        db.execute("PRAGMA user_version = 1")
