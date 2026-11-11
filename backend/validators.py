import re
from typing import Tuple, Optional
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {"txt", "pdf", "docx"}
MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB
MIN_TEXT_LENGTH = 3
MAX_TEXT_LENGTH = 120_000

VALID_PROVIDERS = {"gemini", "openai", "auto"}
VALID_FORMATS = {
    "Executive Summary",
    "Blog Post",
    "Business Report",
    "Presentation Deck",
    "Social Media Campaign",
    "FAQ Guide",
    "Advisory Bulletin",
    "Key Takeaways",
    "Summary",
    "Paraphrase",
    "Grammar",
    "Tone"
}

VALID_TONES = {
    "Professional",
    "Formal",
    "Casual & Friendly",
    "Casual",
    "Academic",
    "Persuasive",
    "Friendly",
    "Confident",
    "Business",
    "Creative",
    "Executive",
    "Technical"
}

VALID_AUDIENCES = {
    "General audience",
    "Business professionals",
    "Technical audience",
    "Students",
    "Government officials",
    "Marketing teams"
}

EMAIL_REGEX = re.compile(r"^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$")

def validate_user_registration(name: str, email: str, password: str, confirm_password: str) -> Tuple[bool, Optional[str]]:
    """Validates registration input fields."""
    if not name or not name.strip():
        return False, "Full name is required."
    if len(name.strip()) < 2:
        return False, "Name must be at least 2 characters."
        
    if not email or not email.strip():
        return False, "Email address is required."
    if not EMAIL_REGEX.match(email.strip()):
        return False, "Please enter a valid email address."
        
    if not password:
        return False, "Password is required."
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
        
    if password != confirm_password:
        return False, "Passwords do not match."
        
    return True, None

def validate_user_login(email: str, password: str) -> Tuple[bool, Optional[str]]:
    """Validates login credentials format."""
    if not email or not email.strip():
        return False, "Email address is required."
    if not password:
        return False, "Password is required."
    return True, None

def validate_text_input(text: Optional[str]) -> Tuple[bool, Optional[str]]:
    """Validates source text payload."""
    if not text or not text.strip():
        return False, "Input content cannot be empty."
    clean = text.strip()
    if len(clean) < MIN_TEXT_LENGTH:
        return False, f"Input content is too short (minimum {MIN_TEXT_LENGTH} characters required)."
    if len(clean) > MAX_TEXT_LENGTH:
        return False, f"Input content exceeds maximum allowed length of {MAX_TEXT_LENGTH} characters."
    return True, None

def validate_file_upload(file_obj: Optional[FileStorage]) -> Tuple[bool, Optional[str]]:
    """Validates uploaded document file type and presence."""
    if not file_obj or not file_obj.filename:
        return False, "No file was selected for upload."
    filename = secure_filename(file_obj.filename)
    if not filename:
        return False, "Invalid file name."
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Unsupported file type (.{ext}). Supported formats are: .txt, .pdf, and .docx."
    return True, None

def validate_provider(provider: Optional[str]) -> Tuple[bool, Optional[str]]:
    """Ensures requested provider is recognized."""
    p = (provider or "auto").strip().lower()
    if p not in VALID_PROVIDERS:
        return False, f"Invalid provider '{provider}'. Must be 'gemini', 'openai', or 'auto'."
    return True, None

def sanitize_string(val: Optional[str], default: str = "") -> str:
    """Safely sanitizes incoming user strings."""
    if not val:
        return default
    # Strip null characters and leading/trailing whitespace
    return val.replace("\x00", "").strip()
