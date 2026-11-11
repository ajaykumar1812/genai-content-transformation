import os
import logging
from typing import Optional, Dict, Any
from config import Config

logger = logging.getLogger("OpenAIService")

class OpenAIService:
    """Official OpenAI Python SDK client wrapper."""

    def __init__(self, api_key: Optional[str] = None, default_model: Optional[str] = None):
        self.api_key = (api_key or Config.OPENAI_API_KEY or "").strip()
        self.default_model = (default_model or Config.OPENAI_MODEL or "gpt-4o-mini").strip()
        self._client = None

    def is_configured(self) -> bool:
        return bool(self.api_key and not self.api_key.startswith("PASTE_"))

    def _get_client(self):
        if not self.is_configured():
            from backend.ai_service import AIServiceAuthError
            raise AIServiceAuthError(
                "OpenAI API key is missing or not configured. "
                "Please add OPENAI_API_KEY to your environment variables or .env file."
            )
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key, timeout=60.0)
            except Exception as e:
                from backend.ai_service import AIServiceError
                raise AIServiceError(f"Failed to initialize OpenAI SDK client: {e}")
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
        Executes an actual OpenAI ChatCompletion request.
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

        # Import specific exceptions from openai
        try:
            from openai import (
                AuthenticationError,
                RateLimitError,
                APITimeoutError,
                APIConnectionError,
                NotFoundError,
                BadRequestError,
                OpenAIError
            )
        except ImportError:
            raise AIServiceError("The 'openai' library is not installed.")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        kwargs = {
            "model": target_model,
            "messages": messages,
            "temperature": temperature
        }
        if max_tokens:
            kwargs["max_tokens"] = max_tokens

        try:
            logger.info("Sending request to OpenAI API with model=%s", target_model)
            response = client.chat.completions.create(**kwargs)

            if not response.choices or not response.choices[0].message:
                raise AIServiceError("OpenAI returned a response with no generated content.")

            output_text = response.choices[0].message.content or ""
            usage_info = {
                "prompt_tokens": getattr(response.usage, "prompt_tokens", 0) if response.usage else 0,
                "completion_tokens": getattr(response.usage, "completion_tokens", 0) if response.usage else 0,
                "total_tokens": getattr(response.usage, "total_tokens", 0) if response.usage else 0
            }

            return {
                "output": output_text.strip(),
                "provider": "OpenAI",
                "model": target_model,
                "usage": usage_info
            }

        except AuthenticationError as e:
            logger.error("OpenAI Authentication Error: %s", str(e))
            raise AIServiceAuthError(
                "OpenAI API authentication failed. The provided API key is invalid, revoked, or lacks permission."
            ) from e
        except RateLimitError as e:
            logger.error("OpenAI Quota/Rate Limit Error: %s", str(e))
            raise AIServiceQuotaError(
                "OpenAI API quota exceeded or rate limit reached. "
                "Please verify your OpenAI credit balance and usage tiers at platform.openai.com."
            ) from e
        except APITimeoutError as e:
            logger.error("OpenAI Timeout Error: %s", str(e))
            raise AIServiceNetworkError(
                "The OpenAI API request timed out waiting for generation to complete."
            ) from e
        except APIConnectionError as e:
            logger.error("OpenAI Connection Error: %s", str(e))
            raise AIServiceNetworkError(
                "Failed to connect to the OpenAI API servers. Please check network connectivity."
            ) from e
        except NotFoundError as e:
            logger.error("OpenAI Model Not Found Error: %s", str(e))
            raise AIServiceModelError(
                f"The requested OpenAI model '{target_model}' was not found or is not accessible with your key."
            ) from e
        except BadRequestError as e:
            logger.error("OpenAI Bad Request Error: %s", str(e))
            raise AIServiceInputError(
                f"OpenAI rejected the input parameters: {e.message}"
            ) from e
        except OpenAIError as e:
            logger.error("OpenAI General Error: %s", str(e))
            raise AIServiceError(f"OpenAI API encountered an error: {str(e)}") from e
        except Exception as e:
            logger.exception("Unexpected error during OpenAI generation: %s", str(e))
            raise AIServiceError(f"Unexpected error communicating with OpenAI: {str(e)}") from e
