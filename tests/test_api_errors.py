import unittest
from unittest.mock import patch
from app import app
from backend.ai_service import (
    AIServiceAuthError, AIServiceQuotaError,
    AIServiceNetworkError, AIServiceModelError
)

class TestAPIErrors(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        self.client = app.test_client()

        # Seed authenticated user session
        with self.client.session_transaction() as sess:
            sess["user_id"] = "test_err_user_id"
            sess["user_name"] = "Error Tester"

    def test_empty_input_handling(self):
        res = self.client.post("/api/transform", data={
            "source_text": "   ",
            "provider": "auto"
        })
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertEqual(data.get("category"), "invalid_input")

    @patch("app.transform_content")
    def test_missing_api_key_error(self, mock_transform):
        mock_transform.side_effect = AIServiceAuthError("Google Gemini API key is missing or not configured.")
        res = self.client.post("/api/transform", data={
            "source_text": "Valid source content text for testing error handling.",
            "provider": "gemini"
        })
        self.assertEqual(res.status_code, 401)
        data = res.get_json()
        self.assertEqual(data.get("category"), "authentication_error")
        self.assertIn("API key is missing", data.get("error"))

    @patch("app.transform_content")
    def test_quota_exceeded_error(self, mock_transform):
        mock_transform.side_effect = AIServiceQuotaError("API quota exceeded or rate limit hit.")
        res = self.client.post("/api/transform", data={
            "source_text": "Valid source content text for testing error handling.",
            "provider": "openai"
        })
        self.assertEqual(res.status_code, 429)
        data = res.get_json()
        self.assertEqual(data.get("category"), "quota_error")

    @patch("app.transform_content")
    def test_network_timeout_error(self, mock_transform):
        mock_transform.side_effect = AIServiceNetworkError("API request timed out waiting for response.")
        res = self.client.post("/api/transform", data={
            "source_text": "Valid source content text for testing error handling.",
            "provider": "gemini"
        })
        self.assertEqual(res.status_code, 503)
        data = res.get_json()
        self.assertEqual(data.get("category"), "network_error")

    @patch("app.transform_content")
    def test_invalid_model_error(self, mock_transform):
        mock_transform.side_effect = AIServiceModelError("Selected model 'deprecated-model-xyz' was not found.")
        res = self.client.post("/api/transform", data={
            "source_text": "Valid source content text for testing error handling.",
            "provider": "gemini"
        })
        self.assertEqual(res.status_code, 404)
        data = res.get_json()
        self.assertEqual(data.get("category"), "model_error")

if __name__ == "__main__":
    unittest.main()
