import os
from functools import wraps
from flask import session, redirect, url_for, flash, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from backend.db import db

def hash_password(password: str) -> str:
    """Hashes a plain-text password using Werkzeug's secure scrypt/pbkdf2."""
    return generate_password_hash(password)

def verify_password(stored_hash: str, password: str) -> bool:
    """Verifies a plain-text password against the stored cryptographic hash."""
    return check_password_hash(stored_hash, password)

def login_required(f):
    """
    Decorator protecting routes from unauthenticated access.
    Returns 401 JSON for API calls; redirects to /login for browser views.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            if request.path.startswith("/api/"):
                return jsonify({
                    "error": "Authentication required. Please sign in to access this feature.",
                    "authenticated": False
                }), 401
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Retrieves the active user record based on the session user_id."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.get_user_by_id(user_id)
