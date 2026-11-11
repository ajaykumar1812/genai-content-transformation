import unittest
import uuid
from app import app
from backend.db import db

class TestAuth(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        self.client = app.test_client()

    def test_registration_and_login_flow(self):
        # 1. Register a new user
        unique_email = f"auth_test_{uuid.uuid4().hex[:6]}@example.com"
        password = "SecurePassword123"
        reg_res = self.client.post("/register", data={
            "name": "Alex Tester",
            "email": unique_email,
            "password": password,
            "confirm_password": password
        }, follow_redirects=True)
        self.assertEqual(reg_res.status_code, 200)
        self.assertIn(b"Alex Tester", reg_res.data)

        # 2. Logout so we are unauthenticated
        logout_res = self.client.get("/logout", follow_redirects=True)
        self.assertEqual(logout_res.status_code, 200)
        self.assertIn(b"Sign In", logout_res.data)

        # 3. Duplicate registration attempt with same email should be rejected
        dup_res = self.client.post("/register", data={
            "name": "Alex Tester",
            "email": unique_email,
            "password": password,
            "confirm_password": password
        })
        self.assertIn(b"already exists", dup_res.data)

        # 4. Login with invalid password
        bad_login = self.client.post("/login", data={
            "email": unique_email,
            "password": "WrongPassword!"
        })
        self.assertIn(b"Invalid email address or password", bad_login.data)

        # 5. Login with valid password
        good_login = self.client.post("/login", data={
            "email": unique_email,
            "password": password
        }, follow_redirects=True)
        self.assertEqual(good_login.status_code, 200)
        self.assertIn(b"Dashboard", good_login.data)

    def test_protected_routes_unauthorized(self):
        # Client without session
        unauth_client = app.test_client()

        # HTML route should redirect to login
        res = unauth_client.get("/dashboard", follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn("/login", res.headers["Location"])

        # API route should return 401 JSON
        api_res = unauth_client.get("/api/history")
        self.assertEqual(api_res.status_code, 401)
        data = api_res.get_json()
        self.assertIn("error", data)

if __name__ == "__main__":
    unittest.main()
