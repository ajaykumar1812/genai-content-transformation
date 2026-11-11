import os
import logging
from typing import Optional, Dict, Any
from config import Config

logger = logging.getLogger("GeminiService")

class GeminiService:
    """Official Google Gen AI SDK wrapper."""

    def __init__(self, api_key: Optional[str] = None, default_model: Optional[str] = None):
        self.api_key = (api_key or Config.GEMINI_API_KEY or "").strip()
        self.default_model = (default_model or Config.GEMINI_MODEL or "gemini-3.8-flash").strip()
        self._client = None

    def is_configured(self) -> bool:
        return bool(self.api_key and not self.api_key.startswith("PASTE_"))

    def _get_client(self):
        if not self.is_configured():
            from backend.ai_service import AIServiceAuthError
            raise AIServiceAuthError(
                "Google Gemini API key is missing or not configured. "
                "Please add GEMINI_API_KEY to your environment variables or .env file."
            )
        if self._client is None:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                from backend.ai_service import AIServiceError
                raise AIServiceError(f"Failed to initialize Google GenAI SDK client: {e}")
        return self._client

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.4,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Executes a real Google Gemini API call using the official google-genai SDK.
        Does NOT use offline simulation or dummy outputs.
        Distinguishes specific API failure types.
        """
        from backend.ai_service import (
            AIServiceAuthError,
            AIServiceQuotaError,
            AIServiceNetworkError,
            AIServiceModelError,
            AIServiceInputError,
            AIServiceError
        )

        client = self._get_client()
        target_model = (model or self.default_model).strip()

        try:
            from google.genai import errors as genai_errors
            from google.genai import types as genai_types
        except ImportError:
            raise AIServiceError("The 'google-genai' SDK library is not installed.")

        # Construct generation configuration
        config_kwargs = {
            "temperature": temperature,
            "system_instruction": system_prompt
        }
        if max_tokens:
            config_kwargs["max_output_tokens"] = max_tokens

        gen_config = genai_types.GenerateContentConfig(**config_kwargs)

        try:
            logger.info("Sending request to Google Gemini API with model=%s", target_model)
            response = client.models.generate_content(
                model=target_model,
                contents=user_prompt,
                config=gen_config
            )

            if not response or not response.text:
                raise AIServiceError("Google Gemini returned an empty response. The content may have triggered safety filters.")

            return {
                "output": response.text.strip(),
                "provider": "Google Gemini",
                "model": target_model,
                "usage": {
                    "prompt_tokens": getattr(response.usage_metadata, "prompt_token_count", 0) if hasattr(response, "usage_metadata") and response.usage_metadata else 0,
                    "completion_tokens": getattr(response.usage_metadata, "candidates_token_count", 0) if hasattr(response, "usage_metadata") and response.usage_metadata else 0,
                    "total_tokens": getattr(response.usage_metadata, "total_token_count", 0) if hasattr(response, "usage_metadata") and response.usage_metadata else 0
                }
            }

        except genai_errors.APIError as e:
            code = getattr(e, "code", None)
            msg = str(e)
            logger.error("Gemini APIError (Code %s): %s", code, msg)

            if code in (401, 403) or "API_KEY_INVALID" in msg or "PERMISSION_DENIED" in msg:
                raise AIServiceAuthError(
                    "Google Gemini API authentication failed. The API key is invalid, revoked, or lacks required permissions."
                ) from e
            elif code == 429 or "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower():
                raise AIServiceQuotaError(
                    "Google Gemini API quota exceeded or rate limit reached. "
                    "Please check your Google AI Studio plan or request quota increase."
                ) from e
            elif code == 404 or "NOT_FOUND" in msg:
                raise AIServiceModelError(
                    f"Selected Gemini model '{target_model}' was not found or is unavailable in your region. "
                    f"Supported models include gemini-3.8-flash (recommended default), gemini-2.5-flash, and gemini-2.5-pro. "
                    f"Please verify model availability with your Gemini API key or update the GEMINI_MODEL setting in .env."
                ) from e
            elif code in (408, 504) or "DEADLINE_EXCEEDED" in msg:
                raise AIServiceNetworkError(
                    "Google Gemini API request timed out waiting for response."
                ) from e
            elif code == 400 or "INVALID_ARGUMENT" in msg:
                raise AIServiceInputError(
                    f"Google Gemini rejected the input parameters: {msg}"
                ) from e
            else:
                raise AIServiceError(f"Google Gemini API error (Code {code}): {msg}") from e

        except Exception as e:
            logger.exception("Unexpected error during Gemini generation: %s", str(e))
            msg = str(e)
            lower_msg = msg.lower()
            if any(term in lower_msg for term in ("connection", "socket", "getaddrinfo", "dns", "network", "connect")):
                raise AIServiceNetworkError(
                    "Network error connecting to Google Gemini API servers. Please check your internet connection."
                ) from e
            raise AIServiceError(f"Error communicating with Google Gemini: {msg}") from e
