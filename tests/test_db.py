import os
import tempfile
import unittest


class TestDb(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        os.environ["ACCESSHUB_DB_PATH"] = os.path.join(self.tmp_dir, "test.db")

        # Import after env var is set, and reload so config picks it up.
        import importlib

        from app import config as config_module
        importlib.reload(config_module)
        from app import db as db_module
        importlib.reload(db_module)
        self.db = db_module
        self.db.init_db()

    def test_create_and_get_user(self):
        user = self.db.create_user("alice")
        self.assertIsNotNone(user.id)
        fetched = self.db.get_user(user.id)
        self.assertEqual(fetched.username, "alice")

    def test_access_request_lifecycle(self):
        user = self.db.create_user("bob")
        role = self.db.create_role("kubernetes-admin", "Full cluster access")

        ar = self.db.create_access_request(user.id, role.id)
        self.assertEqual(ar.status.value, "pending")

        approved = self.db.decide_access_request(ar.id, approve=True, decided_by="admin")
        self.assertEqual(approved.status.value, "approved")
        self.assertIsNotNone(approved.decided_at)

    def test_list_functions(self):
        self.db.create_user("carol")
        self.db.create_role("read-only")
        self.assertEqual(len(self.db.list_users()), 1)
        self.assertEqual(len(self.db.list_roles()), 1)


if __name__ == "__main__":
    unittest.main()
