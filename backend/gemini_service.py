import os
import time
import logging
from typing import Optional, Dict, Any
from config import Config

logger = logging.getLogger("GeminiService")

class GeminiService:
    """Official Google Gen AI SDK wrapper with exponential backoff retry and circuit safety."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: Optional[str] = None,
        max_attempts: Optional[int] = None,
        initial_delay: Optional[float] = None,
        backoff_factor: Optional[float] = None,
        timeout: Optional[float] = None
    ):
        self.api_key = (api_key or Config.GEMINI_API_KEY or "").strip()
        self.default_model = (default_model or Config.GEMINI_MODEL or "gemini-3.8-flash").strip()
        self.max_attempts = max_attempts or getattr(Config, "GEMINI_MAX_RETRIES", 3)
        self.initial_delay = initial_delay if initial_delay is not None else getattr(Config, "GEMINI_RETRY_INITIAL_DELAY", 1.0)
        self.backoff_factor = backoff_factor if backoff_factor is not None else getattr(Config, "GEMINI_RETRY_BACKOFF_FACTOR", 2.0)
        self.timeout = timeout if timeout is not None else getattr(Config, "GEMINI_REQUEST_TIMEOUT", 30.0)
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
        Includes exponential backoff retry logic for temporary 503 (high demand) and 429 errors.
        Does NOT retry invalid API keys (401/403), invalid model errors (404), or malformed inputs (400).
        Preserves original user inputs across retries and logs without exposing secrets.
        Does NOT use offline simulation or dummy outputs.
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

        # Construct generation configuration (preserved across all retry attempts)
        config_kwargs = {
            "temperature": temperature,
            "system_instruction": system_prompt
        }
        if max_tokens:
            config_kwargs["max_output_tokens"] = max_tokens

        gen_config = genai_types.GenerateContentConfig(**config_kwargs)

        start_time = time.time()
        attempt = 0

        while attempt < self.max_attempts:
            attempt += 1
            elapsed = time.time() - start_time
            if elapsed >= self.timeout:
                logger.error(
                    "Provider: Google Gemini | Model: %s | HTTP Status: 504 | Total request timeout (%.1fs) exceeded before attempt %d/%d",
                    target_model, self.timeout, attempt, self.max_attempts
                )
                raise AIServiceNetworkError(f"Google Gemini request timed out after {self.timeout:.1f}s across retry attempts.")

            try:
                logger.info(
                    "Provider: Google Gemini | Model: %s | HTTP Status: Pending | Attempt: %d/%d",
                    target_model, attempt, self.max_attempts
                )
                response = client.models.generate_content(
                    model=target_model,
                    contents=user_prompt,
                    config=gen_config
                )

                if not response or not response.text:
                    raise AIServiceError("Google Gemini returned an empty response. The content may have triggered safety filters.")

                if attempt > 1:
                    logger.info(
                        "Provider: Google Gemini | Model: %s | HTTP Status: 200 | Succeeded on retry attempt %d/%d",
                        target_model, attempt, self.max_attempts
                    )

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
                # Sanitize error message to avoid leaking keys in logs
                safe_msg = msg.replace(self.api_key, "[REDACTED]") if self.api_key else msg
                safe_summary = safe_msg[:120].strip()

                # --- 1. NON-RETRYABLE: Authentication / Key Errors (401, 403) ---
                if code in (401, 403) or "API_KEY_INVALID" in msg or "PERMISSION_DENIED" in msg:
                    logger.error(
                        "Provider: Google Gemini | Model: %s | HTTP Status: %s | Non-retryable authentication error: %s",
                        target_model, code or 401, safe_summary
                    )
                    raise AIServiceAuthError(
                        "Google Gemini API authentication failed. The API key is invalid, revoked, or lacks required permissions."
                    ) from e

                # --- 2. NON-RETRYABLE: Model Not Found / Unavailable (404) ---
                elif code == 404 or "NOT_FOUND" in msg:
                    logger.error(
                        "Provider: Google Gemini | Model: %s | HTTP Status: %s | Non-retryable model error: %s",
                        target_model, code or 404, safe_summary
                    )
                    raise AIServiceModelError(
                        f"Selected Gemini model '{target_model}' was not found or is unavailable in your region. "
                        f"Supported models include gemini-3.8-flash (recommended default), gemini-2.5-flash, and gemini-2.5-pro. "
                        f"Please verify model availability with your Gemini API key or update the GEMINI_MODEL setting in .env."
                    ) from e

                # --- 3. NON-RETRYABLE: Malformed Input / Bad Request (400) ---
                elif code == 400 or "INVALID_ARGUMENT" in msg:
                    logger.error(
                        "Provider: Google Gemini | Model: %s | HTTP Status: %s | Non-retryable input validation error: %s",
                        target_model, code or 400, safe_summary
                    )
                    raise AIServiceInputError(f"Google Gemini rejected the input parameters: {safe_summary}") from e

                # --- 4. RETRYABLE: Temporary Service Unavailable / High Demand (503) ---
                elif code == 503 or "UNAVAILABLE" in msg or "high demand" in msg.lower() or "overloaded" in msg.lower():
                    if attempt < self.max_attempts:
                        delay = self.initial_delay * (self.backoff_factor ** (attempt - 1))
                        remaining = self.timeout - (time.time() - start_time)
                        if remaining <= 0 or delay > remaining:
                            logger.error(
                                "Provider: Google Gemini | Model: %s | HTTP Status: 503 | Timeout (%.1fs) exceeded during retry %d/%d",
                                target_model, self.timeout, attempt, self.max_attempts
                            )
                            raise AIServiceNetworkError(
                                f"Google Gemini service is temporarily unavailable due to high demand (HTTP 503). "
                                f"Request timed out after {self.timeout:.1f}s across retry attempts."
                            ) from e
                        logger.warning(
                            "Provider: Google Gemini | Model: %s | HTTP Status: 503 | Retry Attempt: %d/%d | Backing off %.2fs due to temporary high demand",
                            target_model, attempt, self.max_attempts, delay
                        )
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(
                            "Provider: Google Gemini | Model: %s | HTTP Status: 503 | All %d retry attempts exhausted | Error: %s",
                            target_model, self.max_attempts, safe_summary
                        )
                        raise AIServiceNetworkError(
                            f"Google Gemini service is temporarily unavailable due to high demand (HTTP 503). "
                            f"All {self.max_attempts} retry attempts failed. Please try again in a few moments."
                        ) from e

                # --- 5. RETRYABLE: Rate Limit / Quota Exceeded (429) ---
                elif code == 429 or "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower() or "rate" in msg.lower():
                    if attempt < self.max_attempts:
                        delay = self.initial_delay * (self.backoff_factor ** (attempt - 1))
                        remaining = self.timeout - (time.time() - start_time)
                        if remaining <= 0 or delay > remaining:
                            logger.error(
                                "Provider: Google Gemini | Model: %s | HTTP Status: 429 | Timeout (%.1fs) exceeded during retry %d/%d",
                                target_model, self.timeout, attempt, self.max_attempts
                            )
                            raise AIServiceQuotaError(
                                f"Google Gemini rate limit or quota exceeded (HTTP 429). "
                                f"Request timed out after {self.timeout:.1f}s across retry attempts."
                            ) from e
                        logger.warning(
                            "Provider: Google Gemini | Model: %s | HTTP Status: 429 | Retry Attempt: %d/%d | Backing off %.2fs due to rate limiting",
                            target_model, attempt, self.max_attempts, delay
                        )
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(
                            "Provider: Google Gemini | Model: %s | HTTP Status: 429 | All %d retry attempts exhausted | Error: %s",
                            target_model, self.max_attempts, safe_summary
                        )
                        raise AIServiceQuotaError(
                            f"Google Gemini rate limit or quota exceeded (HTTP 429). "
                            f"All {self.max_attempts} retry attempts failed. Please wait a moment or check your Google AI Studio plan."
                        ) from e

                # --- 6. RETRYABLE: Request Timeouts (408, 504) ---
                elif code in (408, 504) or "DEADLINE_EXCEEDED" in msg:
                    if attempt < self.max_attempts:
                        delay = self.initial_delay * (self.backoff_factor ** (attempt - 1))
                        logger.warning(
                            "Provider: Google Gemini | Model: %s | HTTP Status: %s | Retry Attempt: %d/%d | Backing off %.2fs due to transient timeout",
                            target_model, code or 504, attempt, self.max_attempts, delay
                        )
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(
                            "Provider: Google Gemini | Model: %s | HTTP Status: %s | All %d retry attempts exhausted",
                            target_model, code or 504, self.max_attempts
                        )
                        raise AIServiceNetworkError(
                            f"Google Gemini API request timed out waiting for response. All {self.max_attempts} retry attempts failed."
                        ) from e

                # --- 7. Generic API Errors ---
                else:
                    logger.error(
                        "Provider: Google Gemini | Model: %s | HTTP Status: %s | API error: %s",
                        target_model, code or 500, safe_summary
                    )
                    raise AIServiceError(f"Google Gemini API error (Code {code}): {safe_summary}") from e

            except Exception as e:
                logger.exception("Unexpected exception during Gemini request attempt %d/%d: %s", attempt, self.max_attempts, str(e))
                msg = str(e)
                lower_msg = msg.lower()
                safe_summary = msg[:120].strip()

                if any(term in lower_msg for term in ("connection", "socket", "getaddrinfo", "dns", "network", "connect")):
                    if attempt < self.max_attempts:
                        delay = self.initial_delay * (self.backoff_factor ** (attempt - 1))
                        logger.warning(
                            "Provider: Google Gemini | Model: %s | HTTP Status: NetworkError | Retry Attempt: %d/%d | Backing off %.2fs",
                            target_model, attempt, self.max_attempts, delay
                        )
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(
                            "Provider: Google Gemini | Model: %s | HTTP Status: NetworkError | All %d retry attempts exhausted",
                            target_model, self.max_attempts
                        )
                        raise AIServiceNetworkError(
                            f"Network error connecting to Google Gemini API servers. All {self.max_attempts} retry attempts failed. Please check your internet connection."
                        ) from e

                raise AIServiceError(f"Error communicating with Google Gemini: {safe_summary}") from e
