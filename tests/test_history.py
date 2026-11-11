import unittest
import uuid
from backend.db import db

class TestHistory(unittest.TestCase):
    def setUp(self):
        self.user_a = f"user_a_{uuid.uuid4().hex[:6]}"
        self.user_b = f"user_b_{uuid.uuid4().hex[:6]}"

    def test_history_crud_and_user_isolation(self):
        # 1. Save transformation for User A
        rec1 = db.save_transformation(
            user_id=self.user_a,
            source="Quantum computing algorithms are advancing.",
            output="Quantum computing accelerates complex cryptography.",
            format_type="Summary",
            title="Quantum Summary",
            provider="Google Gemini",
            model="gemini-2.5-flash"
        )
        self.assertIsNotNone(rec1.get("id"))
        rec1_id = rec1["id"]

        # 2. Save transformation for User B
        rec2 = db.save_transformation(
            user_id=self.user_b,
            source="Cybersecurity defenses must be updated.",
            output="Proactive cyber hygiene protects enterprise infrastructure.",
            format_type="Blog Post",
            title="Cybersecurity Blog",
            provider="OpenAI",
            model="gpt-4o-mini"
        )
        rec2_id = rec2["id"]

        # 3. User A retrieves history: should contain only rec1, NOT rec2
        hist_a = db.get_user_history(self.user_a)
        ids_a = [item["id"] for item in hist_a]
        self.assertIn(rec1_id, ids_a)
        self.assertNotIn(rec2_id, ids_a)

        # 4. Search and filter
        search_res = db.get_user_history(self.user_a, search_query="Quantum")
        self.assertEqual(len(search_res), 1)

        filter_res = db.get_user_history(self.user_a, filter_type="Summary")
        self.assertEqual(len(filter_res), 1)

        filter_none = db.get_user_history(self.user_a, filter_type="Blog")
        self.assertEqual(len(filter_none), 0)

        # 5. User A attempts to access User B's record: MUST return None
        unauth_read = db.get_transformation_by_id(rec2_id, user_id=self.user_a)
        self.assertIsNone(unauth_read, "User A must not access User B's transformation!")

        # 6. User A attempts to delete User B's record: MUST return False
        unauth_del = db.delete_transformation(rec2_id, user_id=self.user_a)
        self.assertFalse(unauth_del, "User A must not delete User B's transformation!")

        # 7. User A deletes their own record: MUST return True
        auth_del = db.delete_transformation(rec1_id, user_id=self.user_a)
        self.assertTrue(auth_del)

        # 8. Clear all history for User B
        cleared = db.clear_user_history(self.user_b)
        self.assertTrue(cleared >= 1)
        self.assertEqual(len(db.get_user_history(self.user_b)), 0)

if __name__ == "__main__":
    unittest.main()
