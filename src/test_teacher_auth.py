import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

import app
from teacher_auth import hash_password, verify_password


class TeacherAuthenticationTests(unittest.TestCase):
    def test_password_hash_verifies_only_matching_password(self):
        teacher = hash_password("correct horse battery staple")

        self.assertTrue(verify_password("correct horse battery staple", teacher))
        self.assertFalse(verify_password("incorrect password", teacher))
        self.assertNotIn("password", teacher)

    def test_missing_teacher_session_is_rejected(self):
        with self.assertRaises(HTTPException) as raised:
            app.require_teacher(None)

        self.assertEqual(raised.exception.status_code, 401)

    def test_valid_teacher_session_is_accepted(self):
        app.teacher_sessions["test-token"] = ("teacher@example.edu", 9999999999)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="test-token")

        try:
            self.assertEqual(app.require_teacher(credentials), "test-token")
        finally:
            app.teacher_sessions.pop("test-token", None)

    def test_login_issues_session_and_logout_revokes_it(self):
        teacher = {"username": "coach", **hash_password("correct horse battery staple")}
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="")

        with tempfile.TemporaryDirectory() as temp_dir:
            credentials_file = Path(temp_dir) / "teachers.json"
            credentials_file.write_text(json.dumps({"teachers": [teacher]}), encoding="utf-8")

            with patch.object(app, "teachers_file", credentials_file):
                login_result = app.teacher_login(app.TeacherLogin(
                    username="coach", password="correct horse battery staple"
                ))

            credentials = HTTPAuthorizationCredentials(
                scheme="Bearer", credentials=login_result["access_token"]
            )
            self.assertEqual(app.require_teacher(credentials), login_result["access_token"])
            app.teacher_logout(login_result["access_token"])

            with self.assertRaises(HTTPException) as raised:
                app.require_teacher(credentials)
            self.assertEqual(raised.exception.status_code, 401)

    def test_roster_mutation_routes_require_teacher_dependency(self):
        protected_paths = {
            ("/activities/{activity_name}/signup", "POST"),
            ("/activities/{activity_name}/unregister", "DELETE"),
        }
        routes = {
            (route.path, method): route
            for route in app.app.routes
            for method in getattr(route, "methods", set())
        }

        for path, method in protected_paths:
            with self.subTest(path=path, method=method):
                dependencies = routes[(path, method)].dependant.dependencies
                self.assertIn(app.require_teacher, [dependency.call for dependency in dependencies])


if __name__ == "__main__":
    unittest.main()