import os
from dotenv import load_dotenv

# Load variables from .env file if present
load_dotenv()

class Config:
    """Central application configuration loaded from environment variables."""
    # Web & Session
    SECRET_KEY = os.getenv("SECRET_KEY", "genai-content-transformation-secure-secret-key-2026")
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 5000))
    DEBUG = os.getenv("FLASK_DEBUG", "false").lower() in ("true", "1", "t")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 15 * 1024 * 1024))  # 15 MB
    
    # MongoDB
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    MONGO_DB = os.getenv("MONGO_DB", "genai_content_transformation")
    MONGO_TIMEOUT_MS = int(os.getenv("MONGO_TIMEOUT_MS", 5000))

    # Google Gemini API
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()
    
    # Supported Gemini Models
    # Note: gemini-1.5-flash and gemini-1.5-pro are deprecated and removed.
    # Supported: gemini-3.8-flash (recommended default), gemini-2.5-flash, gemini-2.5-pro
    GEMINI_SUPPORTED_MODELS = [
        {"id": "gemini-3.8-flash", "name": "Gemini 3.8 Flash (Fast, Recommended)"},
        {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash"},
        {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro (Advanced Reasoning)"}
    ]

    # OpenAI API
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
    
    # Supported OpenAI Models
    OPENAI_SUPPORTED_MODELS = [
        {"id": "gpt-4o-mini", "name": "GPT-4o Mini (Fast & Cost-Efficient)"},
        {"id": "gpt-4o", "name": "GPT-4o (High Intelligence Flagship)"},
        {"id": "gpt-4-turbo", "name": "GPT-4 Turbo"},
        {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo"}
    ]

    # Rate Limiting (in-memory requests per minute per IP)
    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", 60))

    @classmethod
    def is_gemini_configured(cls) -> bool:
        return bool(cls.GEMINI_API_KEY and not cls.GEMINI_API_KEY.startswith("PASTE_"))

    @classmethod
    def is_openai_configured(cls) -> bool:
        return bool(cls.OPENAI_API_KEY and not cls.OPENAI_API_KEY.startswith("PASTE_"))

    @classmethod
    def get_configured_providers(cls):
        providers = []
        if cls.is_gemini_configured():
            providers.append("gemini")
        if cls.is_openai_configured():
            providers.append("openai")
        return providers

    @classmethod
    def validate_configuration(cls):
        """Returns a dict detailing configuration readiness without exposing secrets."""
        gemini_ok = cls.is_gemini_configured()
        openai_ok = cls.is_openai_configured()
        
        status = {
            "gemini_configured": gemini_ok,
            "gemini_model": cls.GEMINI_MODEL,
            "openai_configured": openai_ok,
            "openai_model": cls.OPENAI_MODEL,
            "any_provider_configured": gemini_ok or openai_ok,
            "configured_providers": cls.get_configured_providers(),
            "missing_keys": []
        }
        if not gemini_ok:
            status["missing_keys"].append("GEMINI_API_KEY")
        if not openai_ok:
            status["missing_keys"].append("OPENAI_API_KEY")
        return status
