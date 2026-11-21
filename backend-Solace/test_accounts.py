import re
import sqlite3
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash

from app import app
from database import get_db

PASSWORD = "synthetic-password-123"
OTHER_PASSWORD = "different-password-456"
TOKEN_PATTERN = rb'name="csrf_token" value="([^"]+)"'


class AccountTests(unittest.TestCase):
    def setUp(self):
        workspace = tempfile.TemporaryDirectory()
        self.addCleanup(workspace.cleanup)
        self.database = Path(workspace.name) / "test.sqlite3"
        original = app.config.copy()
        self.addCleanup(app.config.update, original)
        app.config.update(TESTING=True, DATABASE=self.database, SESSION_COOKIE_SECURE=False)
        self.browser = app.test_client()

    def migrate(self):
        result = app.test_cli_runner().invoke(args=["migrate-accounts"])
        self.assertEqual(result.exit_code, 0, result.output or repr(result.exception))

    def csrf(self, browser, path="/login"):
        response = browser.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(match := re.search(TOKEN_PATTERN, response.data))
        return match.group(1).decode()

    def register(self, email, **overrides):
        data = dict(name="Client Example", email=email, password=PASSWORD, confirm=PASSWORD, role="client")
        data.update(overrides)
        return self.browser.post("/register", data={**data, "csrf_token": self.csrf(self.browser, "/register")})

    def sign_in(self, browser, email, password=PASSWORD):
        return browser.post("/login", data={
            "email": email, "password": password, "csrf_token": self.csrf(browser),
        })

    def account(self, email):
        with app.app_context(), get_db() as db:
            return db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

    def add_account(self, name, email, role, status="active"):
        with app.app_context(), get_db() as db:
            return db.execute(
                "INSERT INTO users (name, email, password_hash, role, status) VALUES (?, ?, ?, ?, ?)",
                (name, email, generate_password_hash(PASSWORD), role, status),
            ).lastrowid

    def session_headers(self, browser, path):
        return {"X-CSRF-Token": self.csrf(browser, path)}

    def test_public_pages_do_not_initialize_database(self):
        for path in ("/", "/login", "/register", "/search-therapist"):
            self.assertEqual(self.browser.get(path).status_code, 200)
        self.assertEqual(self.register("client@example.invalid").status_code, 503)
        self.assertFalse(self.database.exists())

    def test_registration_hashes_password_and_validates_inputs(self):
        self.migrate()
        response = self.register("  CLIENT@Example.Invalid  ")
        self.assertEqual((response.status_code, response.location), (303, "/login"))
        self.assertIn(b"Account created", self.browser.get("/login").data)
        account = self.account("client@example.invalid")
        self.assertEqual((account["role"], account["status"]), ("client", "active"))
        self.assertNotEqual(account["password_hash"], PASSWORD)
        self.assertTrue(check_password_hash(account["password_hash"], PASSWORD))
        self.assertEqual(self.register("CLIENT@example.invalid").status_code, 409)
        for email, invalid in (
            ("no-domain", {}),
            ("short@example.invalid", {"password": "short"}),
            ("mismatch@example.invalid", {"confirm": OTHER_PASSWORD}),
            ("admin@example.invalid", {"role": "admin"}),
        ):
            with self.subTest(email=email):
                self.assertEqual(self.register(email, **invalid).status_code, 400)
                self.assertIsNone(self.account(email))

    def test_login_rotates_session_and_logout_requires_csrf(self):
        self.migrate()
        account_id = self.add_account("Client Example", "client@example.invalid", "client")
        previous_token = self.csrf(self.browser)
        self.assertEqual(self.sign_in(self.browser, "client@example.invalid", OTHER_PASSWORD).status_code, 401)
        self.assertEqual(self.sign_in(self.browser, "missing@example.invalid").status_code, 401)
        response = self.sign_in(self.browser, "CLIENT@example.invalid")
        self.assertEqual((response.status_code, response.location), (303, "/client"))
        self.assertIn("HttpOnly", response.headers["Set-Cookie"])
        self.assertIn("SameSite=Lax", response.headers["Set-Cookie"])
        with self.browser.session_transaction() as account_session:
            self.assertEqual(account_session["user_id"], account_id)
            self.assertNotIn("csrf_token", account_session)
            self.assertNotIn("role", account_session)
        self.assertEqual(self.browser.get("/logout").status_code, 405)
        self.assertEqual(self.browser.post("/logout", data={"csrf_token": previous_token}).status_code, 403)
        token = self.csrf(self.browser, "/client")
        self.assertNotEqual(token, previous_token)
        self.assertEqual(self.browser.post("/logout", data={"csrf_token": token}).status_code, 303)
        self.assertEqual(self.browser.get("/client").location, "/login")

    def test_pending_therapist_and_suspended_account(self):
        self.migrate()
        self.assertEqual(self.register("pending@example.invalid", role="therapist").status_code, 303)
        self.assertEqual(self.account("pending@example.invalid")["status"], "pending")
        self.assertEqual(self.sign_in(self.browser, "pending@example.invalid").status_code, 403)
        client_id = self.add_account("Client Example", "client@example.invalid", "client")
        self.assertEqual(self.sign_in(self.browser, "client@example.invalid").status_code, 303)
        with app.app_context(), get_db() as db:
            db.execute("UPDATE users SET status = 'suspended' WHERE id = ?", (client_id,))
        self.assertEqual(self.browser.get("/client").status_code, 403)
        self.assertEqual(self.browser.post("/api/appointments", json={}).status_code, 403)
        self.assertEqual(self.sign_in(app.test_client(), "client@example.invalid").status_code, 403)

    def test_role_guards_on_pages_and_apis(self):
        self.migrate()
        paths = {
            "client": ("/client", "/schedule", "/chats"),
            "therapist": ("/therapist", "/therapist/bookings", "/therapist/appointments"),
            "admin": ("/admin", "/admin/dashboard", "/admin/user-management", "/admin/reports", "/admin/therapist-verification"),
        }
        self.assertEqual(self.browser.put("/api/profile/client", json={}).status_code, 401)
        self.assertEqual(self.browser.post("/api/appointments", json={}).status_code, 401)
        self.assertEqual(self.browser.patch("/api/appointments/1", json={}).status_code, 401)
        for role, own_paths in paths.items():
            email = f"{role}@example.invalid"
            self.add_account(f"{role} Example", email, role)
            browser = app.test_client()
            self.assertEqual(self.sign_in(browser, email).location, own_paths[0])
            for owner, protected in paths.items():
                for path in protected:
                    with self.subTest(role=role, path=path):
                        self.assertEqual(self.browser.get(path).location, "/login")
                        response = browser.get(path)
                        expected = 200 if owner == role else 403
                        self.assertEqual(response.status_code, 302 if owner == role and path == "/chats" else expected)
                        self.assertNotIn(b"Switch Role", response.data)
            self.assertEqual(browser.get("/settings?role=admin").status_code, 200)
            if role != "admin":
                self.assertEqual(browser.post("/admin/therapist/verify/1").status_code, 403)
            else:
                headers = self.session_headers(browser, "/admin")
                self.assertEqual(browser.post("/admin/therapist/verify/1").status_code, 403)
                self.assertEqual(browser.post("/admin/therapist/verify/1", headers=headers).status_code, 501)

    def test_admin_is_provisioned_via_cli(self):
        self.migrate()
        result = app.test_cli_runner().invoke(
            args=["create-admin", "--name", "Administrator Example", "--email", "admin@example.invalid"],
            input=f"{PASSWORD}\n{PASSWORD}\n",
        )
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(self.account("admin@example.invalid")["role"], "admin")
        self.assertEqual(self.sign_in(self.browser, "admin@example.invalid").location, "/admin")

    def test_profile_isolation_and_server_controlled_fields(self):
        self.migrate()
        self.add_account("First Account", "first@example.invalid", "client")
        self.add_account("Second Account", "second@example.invalid", "client")
        second = app.test_client()
        self.sign_in(self.browser, "first@example.invalid")
        self.sign_in(second, "second@example.invalid")
        headers = self.session_headers(self.browser, "/profile")
        self.assertEqual(self.browser.put("/api/profile/client", json={"name": "Spoofed"}).status_code, 403)
        self.assertEqual(self.browser.put("/api/profile/admin", headers=headers, json={"name": "Spoofed"}).status_code, 403)
        for field in ("user_id", "email", "role", "status", "access_level"):
            self.assertEqual(self.browser.put("/api/profile/client", headers=headers, json={field: "Spoofed"}).status_code, 400)
        result = self.browser.put("/api/profile/client", headers=headers, json={"name": "Edited First"})
        self.assertEqual(result.status_code, 200)
        self.assertIn(b"Edited First", self.browser.get("/profile?role=admin").data)
        self.assertNotIn(b"Edited First", second.get("/profile").data)
        self.assertIn(b"Second Account", second.get("/profile").data)

    def test_scheduling_uses_account_ownership_and_checks_transitions(self):
        self.migrate()
        client_id = self.add_account("Booking Client", "client@example.invalid", "client")
        self.add_account("Other Client", "other-client@example.invalid", "client")
        therapist_id = self.add_account("Assigned Therapist", "therapist@example.invalid", "therapist")
        self.add_account("Other Therapist", "other-therapist@example.invalid", "therapist")
        pending_id = self.add_account("Pending Therapist", "pending@example.invalid", "therapist", "pending")
        therapist, other_therapist, other_client = (app.test_client() for _ in range(3))
        for browser, email in (
            (self.browser, "client@example.invalid"), (therapist, "therapist@example.invalid"),
            (other_therapist, "other-therapist@example.invalid"), (other_client, "other-client@example.invalid"),
        ):
            self.assertEqual(self.sign_in(browser, email).status_code, 303)

        directory = app.test_client().get("/search-therapist").data
        self.assertIn(b"Assigned Therapist", directory)
        self.assertNotIn(b"Pending Therapist", directory)
        self.assertNotIn(b"therapist@example.invalid", directory)
        schedule = self.browser.get(f"/schedule?therapist={therapist_id}").data
        self.assertIn(f'value="{therapist_id}" selected'.encode(), schedule)

        payload = {
            "therapist_id": therapist_id, "date": (date.today() + timedelta(days=1)).isoformat(),
            "time": "10:00 AM", "client": "Forged identity", "client_email": "forged@example.invalid",
        }
        headers = self.session_headers(self.browser, "/schedule")
        self.assertEqual(self.browser.post("/api/appointments", json=payload).status_code, 403)
        self.assertEqual(self.browser.post("/api/appointments", headers=headers, json={**payload, "date": "2000-01-01"}).status_code, 400)
        self.assertEqual(self.browser.post("/api/appointments", headers=headers, json={**payload, "therapist_id": pending_id}).status_code, 404)
        created = self.browser.post("/api/appointments", headers=headers, json=payload)
        self.assertEqual(created.status_code, 201)
        self.assertEqual(self.browser.post("/api/appointments", headers=headers, json=payload).status_code, 409)
        appointment_id = created.json["id"]
        with app.app_context(), get_db() as db:
            appointment = db.execute("SELECT * FROM appointments WHERE id = ?", (appointment_id,)).fetchone()
            self.assertEqual((appointment["client_id"], appointment["therapist_id"]), (client_id, therapist_id))
            self.assertEqual((appointment["client"], appointment["client_email"]), ("Booking Client", "client@example.invalid"))

        self.assertIn(b"10:00 AM", self.browser.get("/schedule").data)
        self.assertNotIn("10:00 AM Â· Pending".encode(), other_client.get("/schedule").data)
        self.assertIn(b"Booking Client", therapist.get("/therapist/bookings").data)
        self.assertNotIn(b"Booking Client", other_therapist.get("/therapist/appointments").data)
        other_client_headers = self.session_headers(other_client, "/schedule")
        competing = other_client.post("/api/appointments", headers=other_client_headers, json=payload)
        self.assertEqual(competing.status_code, 201)
        api = f"/api/appointments/{appointment_id}"
        therapist_headers = self.session_headers(therapist, "/therapist/bookings")
        other_headers = self.session_headers(other_therapist, "/therapist/bookings")
        self.assertEqual(self.browser.patch(api, headers=headers, json={"status": "Confirmed"}).status_code, 403)
        self.assertEqual(therapist.patch(api, json={"status": "Confirmed"}).status_code, 403)
        self.assertEqual(other_therapist.patch(api, headers=other_headers, json={"status": "Confirmed"}).status_code, 404)
        self.assertEqual(therapist.patch(api, headers=therapist_headers, json={"status": "Completed"}).status_code, 409)
        self.assertEqual(therapist.patch(api, headers=therapist_headers, json={"status": "Confirmed"}).status_code, 200)
        self.assertIn(b"10:00 AM", therapist.get("/therapist").data)
        self.assertIn(b"Confirmed", self.browser.get("/schedule").data)
        self.assertEqual(therapist.patch(
            f"/api/appointments/{competing.json['id']}", headers=therapist_headers, json={"status": "Confirmed"},
        ).status_code, 409)
        self.assertEqual(therapist.patch(api, headers=therapist_headers, json={"status": "Confirmed"}).status_code, 409)
        self.assertEqual(therapist.patch(api, headers=therapist_headers, json={"status": "Completed"}).status_code, 200)

    def test_migration_preserves_legacy_records_and_keeps_them_unassigned(self):
        legacy = (42, "Legacy Client", "legacy@example.invalid", "Legacy Therapist", "2031-05-06",
                  "2:00 PM", "Online consultation", "Confirmed", "Synthetic notes", "2031-04-01")
        db = sqlite3.connect(self.database)
        try:
            with db:
                db.execute("""CREATE TABLE appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT NOT NULL, client_email TEXT NOT NULL,
                    therapist TEXT NOT NULL, date TEXT NOT NULL, time TEXT NOT NULL,
                    session_type TEXT NOT NULL DEFAULT 'Online consultation',
                    status TEXT NOT NULL DEFAULT 'Pending', notes TEXT, created_at TEXT
                )""")
                db.execute("INSERT INTO appointments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", legacy)
                db.execute("CREATE TABLE profiles (role TEXT PRIMARY KEY, data TEXT NOT NULL)")
                db.execute("INSERT INTO profiles VALUES ('client', '{}')")
        finally:
            db.close()
        self.migrate()
        self.migrate()
        self.add_account("Legacy Therapist", "therapist@example.invalid", "therapist")
        self.add_account("Legacy Client", "legacy@example.invalid", "client")
        with app.app_context(), get_db() as connection:
            self.assertEqual(tuple(connection.execute("SELECT * FROM appointments").fetchone()), (*legacy, None, None))
            self.assertEqual(connection.execute("SELECT count(*) FROM profiles").fetchone()[0], 1)
            self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.sign_in(self.browser, "therapist@example.invalid")
        self.assertNotIn(b"Legacy Client", self.browser.get("/therapist/bookings").data)
        headers = self.session_headers(self.browser, "/therapist/bookings")
        self.assertEqual(self.browser.patch("/api/appointments/42", headers=headers, json={"status": "Cancelled"}).status_code, 404)
        client = app.test_client()
        self.sign_in(client, "legacy@example.invalid")
        self.assertNotIn("2031".encode(), client.get("/schedule").data)


if __name__ == "__main__":
    unittest.main()
