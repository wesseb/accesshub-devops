import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request


class TestApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = tempfile.mkdtemp()
        os.environ["ACCESSHUB_DB_PATH"] = os.path.join(cls.tmp_dir, "test.db")
        os.environ["ACCESSHUB_PORT"] = "8099"
        os.environ["ACCESSHUB_ADMIN_TOKEN"] = "test-token"

        import importlib

        from app import config as config_module
        importlib.reload(config_module)
        from app import db as db_module
        importlib.reload(db_module)
        from app import handlers as handlers_module
        importlib.reload(handlers_module)

        from http.server import ThreadingHTTPServer

        db_module.init_db()
        cls.server = ThreadingHTTPServer(("127.0.0.1", 8099), handlers_module.AccessHubHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = "http://127.0.0.1:8099"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def _request(self, method, path, body=None, admin=False):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base_url + path, data=data, method=method)
        req.add_header("Content-Type", "application/json")
        if admin:
            req.add_header("X-Admin-Token", "test-token")
        try:
            with urllib.request.urlopen(req) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_health(self):
        status, payload = self._request("GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(payload["status"], "ok")

    def test_full_access_request_flow(self):
        status, user = self._request("POST", "/users", {"username": "dave"})
        self.assertEqual(status, 201)

        status, role = self._request(
            "POST", "/roles", {"name": "terraform-apply"}, admin=True
        )
        self.assertEqual(status, 201)

        status, req = self._request(
            "POST",
            "/access-requests",
            {"user_id": user["id"], "role_id": role["id"]},
        )
        self.assertEqual(status, 201)
        self.assertEqual(req["status"], "pending")

        status, approved = self._request(
            "POST", f"/access-requests/{req['id']}/approve", admin=True
        )
        self.assertEqual(status, 200)
        self.assertEqual(approved["status"], "approved")

    def test_role_creation_requires_admin(self):
        status, payload = self._request("POST", "/roles", {"name": "no-token"})
        self.assertEqual(status, 403)


if __name__ == "__main__":
    unittest.main()
