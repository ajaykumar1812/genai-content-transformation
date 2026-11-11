import unittest
from unittest.mock import patch, MagicMock
from google.genai import errors as genai_errors
from backend.gemini_service import GeminiService
from backend.ai_service import (
    AIServiceAuthError,
    AIServiceQuotaError,
    AIServiceNetworkError,
    AIServiceModelError,
    AIServiceInputError,
    AIServiceError
)

class TestGeminiReliability(unittest.TestCase):
    """
    Automated test suite verifying Gemini API reliability, exponential backoff,
    retry exhaustion, timeout bounds, and strict non-retry of terminal errors.
    """

    def setUp(self):
        self.service = GeminiService(
            api_key="AIzaSy_fake_test_key_for_unit_tests",
            default_model="gemini-3.8-flash",
            max_attempts=3,
            initial_delay=0.001,  # near-zero delay for instant unit tests
            backoff_factor=2.0,
            timeout=5.0
        )
        self.mock_client = MagicMock()
        self.service._client = self.mock_client

    def _create_mock_response(self, text="Transformed content deliverable"):
        mock_resp = MagicMock()
        mock_resp.text = text
        mock_resp.usage_metadata = MagicMock(prompt_token_count=10, candidates_token_count=20, total_token_count=30)
        return mock_resp

    def test_retry_503_success_on_second_attempt(self):
        """Simulate temporary 503 high demand on 1st attempt, then success on 2nd attempt."""
        err_503 = genai_errors.APIError(503, "The model is overloaded. Please try again later.")
        ok_resp = self._create_mock_response("Success after temporary 503 overload")

        self.mock_client.models.generate_content.side_effect = [err_503, ok_resp]

        result = self.service.generate(
            system_prompt="You are a helper.",
            user_prompt="Summarize this text",
            model="gemini-3.8-flash"
        )

        self.assertEqual(result["output"], "Success after temporary 503 overload")
        self.assertEqual(result["provider"], "Google Gemini")
        self.assertEqual(result["model"], "gemini-3.8-flash")
        self.assertEqual(self.mock_client.models.generate_content.call_count, 2)

    def test_retry_429_success_on_third_attempt(self):
        """Simulate 429 rate limit on attempts 1 and 2, then success on attempt 3."""
        err_429 = genai_errors.APIError(429, "Resource has been exhausted (e.g. check quota).")
        ok_resp = self._create_mock_response("Success on 3rd attempt after 429")

        self.mock_client.models.generate_content.side_effect = [err_429, err_429, ok_resp]

        result = self.service.generate(
            system_prompt="You are a helper.",
            user_prompt="Paraphrase this text"
        )

        self.assertEqual(result["output"], "Success on 3rd attempt after 429")
        self.assertEqual(self.mock_client.models.generate_content.call_count, 3)

    def test_retry_503_exhausted_raises_network_error(self):
        """Simulate persistent 503 unavailable across all 3 attempts -> raises AIServiceNetworkError."""
        err_503 = genai_errors.APIError(503, "Service unavailable due to excessive load")
        self.mock_client.models.generate_content.side_effect = [err_503, err_503, err_503]

        with self.assertRaises(AIServiceNetworkError) as ctx:
            self.service.generate(
                system_prompt="You are a helper.",
                user_prompt="Translate text"
            )

        err_msg = str(ctx.exception)
        self.assertIn("503", err_msg)
        self.assertIn("All 3 retry attempts failed", err_msg)
        self.assertEqual(self.mock_client.models.generate_content.call_count, 3)

    def test_retry_429_exhausted_raises_quota_error(self):
        """Simulate persistent 429 quota exhaustion across all 3 attempts -> raises AIServiceQuotaError."""
        err_429 = genai_errors.APIError(429, "RESOURCE_EXHAUSTED: Quota exceeded")
        self.mock_client.models.generate_content.side_effect = [err_429, err_429, err_429]

        with self.assertRaises(AIServiceQuotaError) as ctx:
            self.service.generate(
                system_prompt="You are a helper.",
                user_prompt="Tone shift"
            )

        err_msg = str(ctx.exception)
        self.assertIn("429", err_msg)
        self.assertIn("All 3 retry attempts failed", err_msg)
        self.assertEqual(self.mock_client.models.generate_content.call_count, 3)

    def test_no_retry_on_401_auth_error(self):
        """Authentication errors (401/403) must FAIL IMMEDIATELY with exactly 1 attempt."""
        err_401 = genai_errors.APIError(401, "API_KEY_INVALID: User key is not recognized")
        self.mock_client.models.generate_content.side_effect = err_401

        with self.assertRaises(AIServiceAuthError) as ctx:
            self.service.generate(
                system_prompt="System instructions",
                user_prompt="Check grammar"
            )

        self.assertIn("authentication failed", str(ctx.exception).lower())
        self.assertEqual(self.mock_client.models.generate_content.call_count, 1)

    def test_no_retry_on_404_model_error(self):
        """Model not found (404) must FAIL IMMEDIATELY with exactly 1 attempt."""
        err_404 = genai_errors.APIError(404, "NOT_FOUND: models/gemini-obsolete is not found")
        self.mock_client.models.generate_content.side_effect = err_404

        with self.assertRaises(AIServiceModelError) as ctx:
            self.service.generate(
                system_prompt="System instructions",
                user_prompt="Generate blog",
                model="gemini-obsolete"
            )

        self.assertIn("was not found or is unavailable", str(ctx.exception))
        self.assertEqual(self.mock_client.models.generate_content.call_count, 1)

    def test_no_retry_on_400_invalid_argument(self):
        """Malformed input (400) must FAIL IMMEDIATELY with exactly 1 attempt."""
        err_400 = genai_errors.APIError(400, "INVALID_ARGUMENT: Prompt violates context length limits")
        self.mock_client.models.generate_content.side_effect = err_400

        with self.assertRaises(AIServiceInputError) as ctx:
            self.service.generate(
                system_prompt="System prompt",
                user_prompt="Malformed content"
            )

        self.assertIn("rejected the input parameters", str(ctx.exception))
        self.assertEqual(self.mock_client.models.generate_content.call_count, 1)

    def test_timeout_stops_retries_gracefully(self):
        """Ensure total request timeout aborts retries when time limit is exceeded."""
        service = GeminiService(
            api_key="AIzaSy_fake_test_key",
            default_model="gemini-3.8-flash",
            max_attempts=5,
            initial_delay=0.2,
            backoff_factor=2.0,
            timeout=0.05  # lower than initial delay
        )
        service._client = self.mock_client
        err_503 = genai_errors.APIError(503, "High demand")
        self.mock_client.models.generate_content.side_effect = err_503

        with self.assertRaises(AIServiceNetworkError) as ctx:
            service.generate(
                system_prompt="System prompt",
                user_prompt="Prompt"
            )

        self.assertIn("timed out", str(ctx.exception).lower())
        self.assertEqual(self.mock_client.models.generate_content.call_count, 1)

    def test_input_preservation_across_retries(self):
        """Verifies original prompts and configs are preserved identically across retry attempts."""
        err_503 = genai_errors.APIError(503, "Service busy")
        ok_resp = self._create_mock_response("Final preserved answer")
        self.mock_client.models.generate_content.side_effect = [err_503, ok_resp]

        self.service.generate(
            system_prompt="Preserved System Instruction",
            user_prompt="Preserved User Input Prompt",
            model="gemini-3.8-flash",
            temperature=0.7,
            max_tokens=2048
        )

        calls = self.mock_client.models.generate_content.call_args_list
        self.assertEqual(len(calls), 2)
        for c in calls:
            kwargs = c.kwargs
            self.assertEqual(kwargs["model"], "gemini-3.8-flash")
            self.assertEqual(kwargs["contents"], "Preserved User Input Prompt")
            self.assertEqual(kwargs["config"].system_instruction, "Preserved System Instruction")
            self.assertEqual(kwargs["config"].temperature, 0.7)
            self.assertEqual(kwargs["config"].max_output_tokens, 2048)

if __name__ == "__main__":
    unittest.main()
