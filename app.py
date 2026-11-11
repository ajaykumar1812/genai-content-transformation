import os
import time
from collections import defaultdict
from datetime import datetime, timezone
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, jsonify, send_file
)
from config import Config
from backend.db import db
from backend.auth import (
    hash_password, verify_password, login_required, get_current_user
)
from backend.validators import (
    validate_user_registration, validate_user_login,
    validate_text_input, validate_file_upload,
    validate_provider, sanitize_string
)
from backend.document_parser import extract_document_text, get_document_metadata
from backend.ai_service import (
    transform_content, summarize_text, paraphrase_text,
    correct_grammar, transform_tone, generate_blog,
    generate_executive_summary, generate_business_report,
    generate_presentation, generate_faq, generate_key_takeaways,
    generate_social_media, get_active_provider_status,
    AIServiceError, AIServiceAuthError, AIServiceQuotaError,
    AIServiceNetworkError, AIServiceModelError, AIServiceInputError
)
from backend.exporters import (
    export_as_txt, export_as_docx, export_as_pdf, export_as_pptx
)

# Initialize Flask application
app = Flask(__name__)
app.secret_key = Config.SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = Config.MAX_CONTENT_LENGTH
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# In-memory rate limiter per IP for AI endpoints (sliding window)
_rate_limit_records = defaultdict(list)

def check_rate_limit(client_ip: str) -> bool:
    """Returns False if client IP has exceeded max requests per minute."""
    now = time.time()
    cutoff = now - 60.0
    # Clean old entries
    _rate_limit_records[client_ip] = [t for t in _rate_limit_records[client_ip] if t > cutoff]
    if len(_rate_limit_records[client_ip]) >= Config.RATE_LIMIT_PER_MINUTE:
        return False
    _rate_limit_records[client_ip].append(now)
    return True

@app.before_request
def enforce_rate_limiting():
    if request.path.startswith("/api/ai/") or request.path.startswith("/api/transform"):
        client_ip = request.headers.get("X-Forwarded-For", request.remote_addr or "127.0.0.1").split(",")[0].strip()
        if not check_rate_limit(client_ip):
            return jsonify({
                "error": "Rate limit exceeded. Please wait a moment before sending another AI request.",
                "category": "rate_limit"
            }), 429

@app.context_processor
def inject_global_data():
    user = get_current_user()
    user_settings = db.get_user_settings(user["id"]) if user else {
        "preferred_provider": "gemini" if Config.is_gemini_configured() else ("openai" if Config.is_openai_configured() else "gemini"),
        "preferred_model": Config.GEMINI_MODEL,
        "theme": "dark"
    }
    status = get_active_provider_status()
    status["mongodb_connected"] = db.is_connected
    return {
        "current_user": user,
        "user_settings": user_settings,
        "system_status": status,
        "app_config": Config,
        "now": datetime.now()
    }

# ==============================================================================
# ERROR HANDLERS (Standard JSON format for API routes)
# ==============================================================================

@app.errorhandler(413)
def request_entity_too_large(e):
    if request.path.startswith("/api/"):
        return jsonify({"error": "File size exceeds the 15 MB upload limit."}), 413
    flash("The uploaded file exceeds the 15 MB limit.", "danger")
    return redirect(request.url)

@app.errorhandler(404)
def page_not_found(e):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Requested API endpoint not found."}), 404
    return render_template("index.html"), 404

# ==============================================================================
# WEB UI VIEW ROUTES
# ==============================================================================

@app.get("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        valid, err = validate_user_login(email, password)
        if not valid:
            flash(err, "warning")
            return render_template("login.html", email=email)

        user = db.get_user_by_email(email)
        if not user or not verify_password(user["password_hash"], password):
            flash("Invalid email address or password. Please try again.", "danger")
            return render_template("login.html", email=email)

        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        flash(f"Welcome back, {user['name']}!", "success")
        next_url = request.args.get("next") or url_for("dashboard")
        return redirect(next_url)
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm_password") or ""

        valid, err = validate_user_registration(name, email, password, confirm)
        if not valid:
            flash(err, "warning")
            return render_template("register.html", name=name, email=email)

        try:
            pwd_hash = hash_password(password)
            user_id = db.create_user(name, email, pwd_hash)
            session["user_id"] = user_id
            session["user_name"] = name
            flash("Account created successfully! Welcome to your Gen AI Workspace.", "success")
            return redirect(url_for("dashboard"))
        except ValueError as e:
            flash(str(e), "danger")
        except Exception as e:
            flash(f"Registration error: {str(e)}", "danger")

    return render_template("register.html")

@app.get("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("login"))

@app.get("/dashboard")
@login_required
def dashboard():
    user_id = session.get("user_id")
    stats = db.get_dashboard_stats(user_id)
    return render_template("dashboard.html", stats=stats)

@app.get("/studio")
@login_required
def studio():
    return render_template("studio.html")

@app.get("/summarizer")
@login_required
def summarizer():
    return render_template("summarizer.html")

@app.get("/paraphraser")
@login_required
def paraphraser():
    return render_template("paraphraser.html")

@app.get("/tone")
@login_required
def tone():
    return render_template("tone.html")

@app.get("/grammar")
@login_required
def grammar():
    return render_template("grammar.html")

@app.get("/documents")
@login_required
def documents():
    return render_template("documents.html")

@app.get("/history")
@login_required
def history():
    user_id = session.get("user_id")
    search_q = request.args.get("q", "")
    filter_t = request.args.get("type", "")
    items = db.get_user_history(user_id, limit=100, search_query=search_q, filter_type=filter_t)
    return render_template("history.html", items=items, search_q=search_q, filter_t=filter_t)

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    user_id = session.get("user_id")
    user = get_current_user()
    current_settings = db.get_user_settings(user_id)

    if request.method == "POST":
        provider = request.form.get("preferred_provider", "gemini")
        model = request.form.get("preferred_model", Config.GEMINI_MODEL)
        theme = request.form.get("theme", "dark")
        db.save_user_settings(user_id, provider, model, theme)
        flash("Your settings and AI preferences have been updated.", "success")
        return redirect(url_for("settings"))

    return render_template("settings.html", user=user, settings=current_settings)

# ==============================================================================
# REST API: AUTHENTICATION
# ==============================================================================

@app.post("/api/auth/register")
def api_auth_register():
    data = request.get_json(silent=True) or request.form
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    confirm = data.get("confirm_password") or password

    valid, err = validate_user_registration(name, email, password, confirm)
    if not valid:
        return jsonify({"error": err}), 400

    try:
        pwd_hash = hash_password(password)
        user_id = db.create_user(name, email, pwd_hash)
        session["user_id"] = user_id
        session["user_name"] = name
        return jsonify({
            "success": True,
            "message": "User registered successfully.",
            "user": {"id": user_id, "name": name, "email": email}
        }), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 409
    except Exception as e:
        return jsonify({"error": f"Registration error: {str(e)}"}), 500

@app.post("/api/auth/login")
def api_auth_login():
    data = request.get_json(silent=True) or request.form
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    valid, err = validate_user_login(email, password)
    if not valid:
        return jsonify({"error": err}), 400

    user = db.get_user_by_email(email)
    if not user or not verify_password(user["password_hash"], password):
        return jsonify({"error": "Invalid email address or password."}), 401

    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    return jsonify({
        "success": True,
        "message": "Authentication successful.",
        "user": {"id": user["id"], "name": user["name"], "email": user["email"]}
    })

@app.post("/api/auth/logout")
def api_auth_logout():
    session.clear()
    return jsonify({"success": True, "message": "Signed out successfully."})

@app.get("/api/auth/me")
def api_auth_me():
    user = get_current_user()
    if not user:
        return jsonify({"authenticated": False}), 200
    settings = db.get_user_settings(user["id"])
    return jsonify({
        "authenticated": True,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "created_at": user.get("created_at")
        },
        "settings": settings
    })

# ==============================================================================
# REST API: DOCUMENT EXTRACTION & UPLOAD
# ==============================================================================

@app.post("/api/documents/upload")
@login_required
def api_documents_upload():
    uploaded_file = request.files.get("file")
    valid, err = validate_file_upload(uploaded_file)
    if not valid:
        return jsonify({"error": err}), 400

    try:
        metadata = get_document_metadata(uploaded_file)
        return jsonify({
            "success": True,
            "filename": metadata["filename"],
            "character_count": metadata["character_count"],
            "word_count": metadata["word_count"],
            "preview": metadata["preview"],
            "text": metadata["full_text"]
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Document processing failed: {str(e)}"}), 500

@app.post("/api/documents/extract")
def api_documents_extract():
    uploaded_file = request.files.get("file")
    valid, err = validate_file_upload(uploaded_file)
    if not valid:
        return jsonify({"error": err}), 400
    try:
        text = extract_document_text(uploaded_file)
        return jsonify({
            "success": True,
            "text": text,
            "word_count": len(text.split()),
            "character_count": len(text)
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Extraction error: {str(e)}"}), 500

# ==============================================================================
# REST API: AI CONTENT TRANSFORMATION (ONLINE AI ONLY)
# ==============================================================================

def _handle_ai_error(e: Exception):
    """Formats AI errors into structured JSON with distinct error categories."""
    if isinstance(e, AIServiceError):
        return jsonify({
            "error": str(e),
            "category": e.category,
            "status_code": e.status_code
        }), e.status_code
    return jsonify({
        "error": f"An unexpected error occurred during AI processing: {str(e)}",
        "category": "unexpected_error"
    }), 500

def _extract_source_text_from_request() -> str:
    """Extracts source text either from form field or uploaded file."""
    source_text = (request.form.get("source_text") or "").strip()
    uploaded_file = request.files.get("file")
    if uploaded_file and uploaded_file.filename:
        valid, err = validate_file_upload(uploaded_file)
        if not valid:
            raise ValueError(err)
        extracted = extract_document_text(uploaded_file).strip()
        if extracted:
            source_text = extracted
    return source_text

@app.post("/api/transform")
@app.post("/api/ai/transform")
@login_required
def api_transform():
    user_id = session.get("user_id")
    try:
        source_text = _extract_source_text_from_request()
        valid, err = validate_text_input(source_text)
        if not valid:
            return jsonify({"error": err, "category": "invalid_input"}), 400

        output_format = sanitize_string(request.form.get("output_format"), "Executive Summary")
        audience = sanitize_string(request.form.get("audience"), "General audience")
        tone_val = sanitize_string(request.form.get("tone"), "Professional")
        detail = sanitize_string(request.form.get("detail"), "Medium")
        provider = sanitize_string(request.form.get("provider"), "auto")
        model = sanitize_string(request.form.get("model"), "") or None

        output, engine_label, model_name = transform_content(
            source=source_text,
            output_format=output_format,
            audience=audience,
            tone=tone_val,
            detail=detail,
            provider=provider,
            model=model
        )

        saved = db.save_transformation(
            user_id=user_id,
            source=source_text,
            output=output,
            format_type=output_format,
            audience=audience,
            tone=tone_val,
            detail=detail,
            title=f"{output_format} Deliverable",
            provider=engine_label,
            model=model_name
        )

        return jsonify({
            "success": True,
            "output": output,
            "engine": f"{engine_label} ({model_name})",
            "provider": engine_label,
            "model": model_name,
            "format": output_format,
            "id": saved.get("id"),
            "words_input": len(source_text.split()),
            "words_output": len(output.split())
        })

    except ValueError as ve:
        return jsonify({"error": str(ve), "category": "invalid_input"}), 400
    except Exception as e:
        return _handle_ai_error(e)

@app.post("/api/summarize")
@app.post("/api/ai/summarize")
@login_required
def api_summarize():
    user_id = session.get("user_id")
    try:
        source_text = _extract_source_text_from_request()
        valid, err = validate_text_input(source_text)
        if not valid:
            return jsonify({"error": err, "category": "invalid_input"}), 400

        summary_type = sanitize_string(request.form.get("summary_type"), "Executive Summary")
        detail = sanitize_string(request.form.get("detail"), "Medium")
        provider = sanitize_string(request.form.get("provider"), "auto")
        model = sanitize_string(request.form.get("model"), "") or None

        output, engine_label, model_name = summarize_text(
            source=source_text,
            summary_type=summary_type,
            detail=detail,
            provider=provider,
            model=model
        )

        saved = db.save_transformation(
            user_id=user_id,
            source=source_text,
            output=output,
            format_type=f"Summary: {summary_type}",
            audience="General",
            tone="Analytical",
            detail=detail,
            title=f"Summary ({summary_type})",
            provider=engine_label,
            model=model_name
        )

        return jsonify({
            "success": True,
            "output": output,
            "engine": f"{engine_label} ({model_name})",
            "provider": engine_label,
            "model": model_name,
            "id": saved.get("id"),
            "words_input": len(source_text.split()),
            "words_output": len(output.split())
        })

    except ValueError as ve:
        return jsonify({"error": str(ve), "category": "invalid_input"}), 400
    except Exception as e:
        return _handle_ai_error(e)

@app.post("/api/paraphrase")
@app.post("/api/ai/paraphrase")
@login_required
def api_paraphrase():
    user_id = session.get("user_id")
    try:
        source_text = _extract_source_text_from_request()
        valid, err = validate_text_input(source_text)
        if not valid:
            return jsonify({"error": err, "category": "invalid_input"}), 400

        style = sanitize_string(request.form.get("style"), "Standard")
        provider = sanitize_string(request.form.get("provider"), "auto")
        model = sanitize_string(request.form.get("model"), "") or None

        output, engine_label, model_name = paraphrase_text(
            source=source_text,
            style=style,
            provider=provider,
            model=model
        )

        saved = db.save_transformation(
            user_id=user_id,
            source=source_text,
            output=output,
            format_type=f"Paraphrase: {style}",
            audience="General",
            tone=style,
            title=f"Paraphrase ({style})",
            provider=engine_label,
            model=model_name
        )

        return jsonify({
            "success": True,
            "output": output,
            "engine": f"{engine_label} ({model_name})",
            "provider": engine_label,
            "model": model_name,
            "id": saved.get("id"),
            "words_input": len(source_text.split()),
            "words_output": len(output.split())
        })

    except ValueError as ve:
        return jsonify({"error": str(ve), "category": "invalid_input"}), 400
    except Exception as e:
        return _handle_ai_error(e)

@app.post("/api/grammar")
@app.post("/api/ai/grammar")
@login_required
def api_grammar():
    user_id = session.get("user_id")
    try:
        source_text = _extract_source_text_from_request()
        valid, err = validate_text_input(source_text)
        if not valid:
            return jsonify({"error": err, "category": "invalid_input"}), 400

        provider = sanitize_string(request.form.get("provider"), "auto")
        model = sanitize_string(request.form.get("model"), "") or None

        output, engine_label, model_name = correct_grammar(
            source=source_text,
            provider=provider,
            model=model
        )

        saved = db.save_transformation(
            user_id=user_id,
            source=source_text,
            output=output,
            format_type="Grammar Correction",
            audience="General",
            tone="Corrected",
            title="Grammar & Clarity Fix",
            provider=engine_label,
            model=model_name
        )

        return jsonify({
            "success": True,
            "output": output,
            "engine": f"{engine_label} ({model_name})",
            "provider": engine_label,
            "model": model_name,
            "id": saved.get("id"),
            "words_input": len(source_text.split()),
            "words_output": len(output.split())
        })

    except ValueError as ve:
        return jsonify({"error": str(ve), "category": "invalid_input"}), 400
    except Exception as e:
        return _handle_ai_error(e)

@app.post("/api/tone")
@app.post("/api/ai/tone")
@login_required
def api_tone():
    user_id = session.get("user_id")
    try:
        source_text = _extract_source_text_from_request()
        valid, err = validate_text_input(source_text)
        if not valid:
            return jsonify({"error": err, "category": "invalid_input"}), 400

        target_tone = sanitize_string(request.form.get("tone"), "Professional")
        audience = sanitize_string(request.form.get("audience"), "General audience")
        provider = sanitize_string(request.form.get("provider"), "auto")
        model = sanitize_string(request.form.get("model"), "") or None

        output, engine_label, model_name = transform_tone(
            source=source_text,
            target_tone=target_tone,
            audience=audience,
            provider=provider,
            model=model
        )

        saved = db.save_transformation(
            user_id=user_id,
            source=source_text,
            output=output,
            format_type=f"Tone: {target_tone}",
            audience=audience,
            tone=target_tone,
            title=f"Tone Shift ({target_tone})",
            provider=engine_label,
            model=model_name
        )

        return jsonify({
            "success": True,
            "output": output,
            "engine": f"{engine_label} ({model_name})",
            "provider": engine_label,
            "model": model_name,
            "id": saved.get("id"),
            "words_input": len(source_text.split()),
            "words_output": len(output.split())
        })

    except ValueError as ve:
        return jsonify({"error": str(ve), "category": "invalid_input"}), 400
    except Exception as e:
        return _handle_ai_error(e)

@app.post("/api/ai/generate-blog")
@login_required
def api_generate_blog():
    user_id = session.get("user_id")
    try:
        source_text = _extract_source_text_from_request()
        valid, err = validate_text_input(source_text)
        if not valid:
            return jsonify({"error": err, "category": "invalid_input"}), 400

        tone = sanitize_string(request.form.get("tone"), "Engaging")
        length = sanitize_string(request.form.get("length"), "Medium")
        provider = sanitize_string(request.form.get("provider"), "auto")
        model = sanitize_string(request.form.get("model"), "") or None

        output, engine_label, model_name = generate_blog(source_text, tone=tone, target_length=length, provider=provider, model=model)
        saved = db.save_transformation(
            user_id=user_id, source=source_text, output=output,
            format_type="Blog Post", tone=tone, detail=length, title="SEO Blog Post",
            provider=engine_label, model=model_name
        )
        return jsonify({
            "success": True, "output": output, "engine": f"{engine_label} ({model_name})",
            "provider": engine_label, "model": model_name, "id": saved.get("id")
        })
    except Exception as e:
        return _handle_ai_error(e)

@app.post("/api/ai/generate-report")
@login_required
def api_generate_report():
    user_id = session.get("user_id")
    try:
        source_text = _extract_source_text_from_request()
        valid, err = validate_text_input(source_text)
        if not valid:
            return jsonify({"error": err, "category": "invalid_input"}), 400

        detail = sanitize_string(request.form.get("detail"), "Medium")
        provider = sanitize_string(request.form.get("provider"), "auto")
        model = sanitize_string(request.form.get("model"), "") or None

        output, engine_label, model_name = generate_business_report(source_text, detail=detail, provider=provider, model=model)
        saved = db.save_transformation(
            user_id=user_id, source=source_text, output=output,
            format_type="Business Report", detail=detail, title="Corporate Business Report",
            provider=engine_label, model=model_name
        )
        return jsonify({
            "success": True, "output": output, "engine": f"{engine_label} ({model_name})",
            "provider": engine_label, "model": model_name, "id": saved.get("id")
        })
    except Exception as e:
        return _handle_ai_error(e)

@app.post("/api/ai/generate-presentation")
@login_required
def api_generate_presentation():
    user_id = session.get("user_id")
    try:
        source_text = _extract_source_text_from_request()
        valid, err = validate_text_input(source_text)
        if not valid:
            return jsonify({"error": err, "category": "invalid_input"}), 400

        slides = int(request.form.get("slides") or 7)
        provider = sanitize_string(request.form.get("provider"), "auto")
        model = sanitize_string(request.form.get("model"), "") or None

        output, engine_label, model_name = generate_presentation(source_text, num_slides=slides, provider=provider, model=model)
        saved = db.save_transformation(
            user_id=user_id, source=source_text, output=output,
            format_type="Presentation Deck", title="Presentation Deck Content",
            provider=engine_label, model=model_name
        )
        return jsonify({
            "success": True, "output": output, "engine": f"{engine_label} ({model_name})",
            "provider": engine_label, "model": model_name, "id": saved.get("id")
        })
    except Exception as e:
        return _handle_ai_error(e)

@app.post("/api/ai/generate-faq")
@login_required
def api_generate_faq():
    user_id = session.get("user_id")
    try:
        source_text = _extract_source_text_from_request()
        valid, err = validate_text_input(source_text)
        if not valid:
            return jsonify({"error": err, "category": "invalid_input"}), 400

        provider = sanitize_string(request.form.get("provider"), "auto")
        model = sanitize_string(request.form.get("model"), "") or None

        output, engine_label, model_name = generate_faq(source_text, provider=provider, model=model)
        saved = db.save_transformation(
            user_id=user_id, source=source_text, output=output,
            format_type="FAQ Guide", title="Frequently Asked Questions",
            provider=engine_label, model=model_name
        )
        return jsonify({
            "success": True, "output": output, "engine": f"{engine_label} ({model_name})",
            "provider": engine_label, "model": model_name, "id": saved.get("id")
        })
    except Exception as e:
        return _handle_ai_error(e)

@app.post("/api/ai/generate-takeaways")
@login_required
def api_generate_takeaways():
    user_id = session.get("user_id")
    try:
        source_text = _extract_source_text_from_request()
        valid, err = validate_text_input(source_text)
        if not valid:
            return jsonify({"error": err, "category": "invalid_input"}), 400

        provider = sanitize_string(request.form.get("provider"), "auto")
        model = sanitize_string(request.form.get("model"), "") or None

        output, engine_label, model_name = generate_key_takeaways(source_text, provider=provider, model=model)
        saved = db.save_transformation(
            user_id=user_id, source=source_text, output=output,
            format_type="Key Takeaways", title="Key Strategic Takeaways",
            provider=engine_label, model=model_name
        )
        return jsonify({
            "success": True, "output": output, "engine": f"{engine_label} ({model_name})",
            "provider": engine_label, "model": model_name, "id": saved.get("id")
        })
    except Exception as e:
        return _handle_ai_error(e)

@app.post("/api/ai/generate-social")
@login_required
def api_generate_social():
    user_id = session.get("user_id")
    try:
        source_text = _extract_source_text_from_request()
        valid, err = validate_text_input(source_text)
        if not valid:
            return jsonify({"error": err, "category": "invalid_input"}), 400

        platform = sanitize_string(request.form.get("platform"), "LinkedIn")
        tone = sanitize_string(request.form.get("tone"), "Professional")
        provider = sanitize_string(request.form.get("provider"), "auto")
        model = sanitize_string(request.form.get("model"), "") or None

        output, engine_label, model_name = generate_social_media(source_text, platform=platform, tone=tone, provider=provider, model=model)
        saved = db.save_transformation(
            user_id=user_id, source=source_text, output=output,
            format_type=f"Social Media: {platform}", tone=tone, title=f"Social Campaign ({platform})",
            provider=engine_label, model=model_name
        )
        return jsonify({
            "success": True, "output": output, "engine": f"{engine_label} ({model_name})",
            "provider": engine_label, "model": model_name, "id": saved.get("id")
        })
    except Exception as e:
        return _handle_ai_error(e)

# ==============================================================================
# REST API: TRANSFORMATION HISTORY
# ==============================================================================

@app.get("/api/history")
@login_required
def api_history():
    user_id = session.get("user_id")
    search_q = request.args.get("q", "")
    filter_t = request.args.get("type", "")
    limit = int(request.args.get("limit", 50))
    items = db.get_user_history(user_id=user_id, limit=limit, search_query=search_q, filter_type=filter_t)
    return jsonify({"success": True, "items": items, "count": len(items)})

@app.get("/api/history/<item_id>")
@login_required
def api_history_item(item_id):
    user_id = session.get("user_id")
    item = db.get_transformation_by_id(item_id, user_id=user_id)
    if not item:
        return jsonify({"error": "Transformation record not found."}), 404
    return jsonify({"success": True, "item": item})

@app.delete("/api/history/<item_id>")
@login_required
def api_delete_history(item_id):
    user_id = session.get("user_id")
    success = db.delete_transformation(item_id, user_id=user_id)
    if not success:
        return jsonify({"error": "Failed to delete record or record not found."}), 404
    return jsonify({"success": True, "message": "Record deleted successfully."})

@app.delete("/api/history")
@app.post("/api/history/clear")
@login_required
def api_clear_history():
    user_id = session.get("user_id")
    count = db.clear_user_history(user_id)
    return jsonify({"success": True, "deleted_count": count})

# ==============================================================================
# REST API: USER SETTINGS
# ==============================================================================

@app.get("/api/settings")
@login_required
def api_get_settings():
    user_id = session.get("user_id")
    settings = db.get_user_settings(user_id)
    return jsonify({"success": True, "settings": settings})

@app.post("/api/settings")
@login_required
def api_save_settings():
    user_id = session.get("user_id")
    data = request.get_json(silent=True) or request.form
    provider = sanitize_string(data.get("preferred_provider"), "gemini")
    model = sanitize_string(data.get("preferred_model"), Config.GEMINI_MODEL)
    theme = sanitize_string(data.get("theme"), "dark")

    success = db.save_user_settings(user_id, provider, model, theme)
    if not success:
        return jsonify({"error": "Failed to update settings."}), 500
    return jsonify({
        "success": True,
        "message": "Settings updated successfully.",
        "settings": {"preferred_provider": provider, "preferred_model": model, "theme": theme}
    })

# ==============================================================================
# REST API: EXPORT FUNCTIONALITY
# ==============================================================================

def _export_dispatch(fmt: str, content: str, title: str):
    fmt = fmt.lower()
    if fmt == "docx":
        return export_as_docx(title, content)
    elif fmt == "pdf":
        return export_as_pdf(title, content)
    elif fmt == "pptx":
        return export_as_pptx(title, content)
    else:
        return export_as_txt(content, title=title)

@app.post("/api/export")
def api_export_unified():
    data = request.get_json(silent=True) or {}
    content = (data.get("content") or request.form.get("content") or "").strip()
    fmt = (data.get("type") or data.get("format") or request.form.get("type") or "txt").lower()
    title = (data.get("title") or request.form.get("title") or "Gen AI Transformed Content").strip()

    if not content:
        return jsonify({"error": "No content available to export."}), 400

    buffer, mimetype, filename = _export_dispatch(fmt, content, title)
    return send_file(buffer, mimetype=mimetype, as_attachment=True, download_name=filename)

@app.post("/api/export/txt")
def api_export_txt():
    data = request.get_json(silent=True) or {}
    content = (data.get("content") or request.form.get("content") or "").strip()
    title = (data.get("title") or request.form.get("title") or "Transformed Content").strip()
    if not content:
        return jsonify({"error": "No content available to export."}), 400
    buffer, mimetype, filename = export_as_txt(content, title=title)
    return send_file(buffer, mimetype=mimetype, as_attachment=True, download_name=filename)

@app.post("/api/export/docx")
def api_export_docx():
    data = request.get_json(silent=True) or {}
    content = (data.get("content") or request.form.get("content") or "").strip()
    title = (data.get("title") or request.form.get("title") or "Transformed Content").strip()
    if not content:
        return jsonify({"error": "No content available to export."}), 400
    buffer, mimetype, filename = export_as_docx(title, content)
    return send_file(buffer, mimetype=mimetype, as_attachment=True, download_name=filename)

@app.post("/api/export/pdf")
def api_export_pdf():
    data = request.get_json(silent=True) or {}
    content = (data.get("content") or request.form.get("content") or "").strip()
    title = (data.get("title") or request.form.get("title") or "Transformed Content").strip()
    if not content:
        return jsonify({"error": "No content available to export."}), 400
    buffer, mimetype, filename = export_as_pdf(title, content)
    return send_file(buffer, mimetype=mimetype, as_attachment=True, download_name=filename)

@app.post("/api/export/pptx")
def api_export_pptx():
    data = request.get_json(silent=True) or {}
    content = (data.get("content") or request.form.get("content") or "").strip()
    title = (data.get("title") or request.form.get("title") or "Presentation").strip()
    if not content:
        return jsonify({"error": "No content available to export."}), 400
    buffer, mimetype, filename = export_as_pptx(title, content)
    return send_file(buffer, mimetype=mimetype, as_attachment=True, download_name=filename)

# ==============================================================================
# REST API: SYSTEM HEALTH & PROVIDER STATUS
# ==============================================================================

@app.get("/api/health")
def api_health():
    status = get_active_provider_status()
    status["mongodb"] = db.is_connected
    status["storage_mode"] = "MongoDB Atlas" if db.is_connected else "Local Storage Fallback"
    status["app_name"] = "Gen AI Platform for Automated Content Transformation"
    status["version"] = "2.0.0"
    return jsonify(status)

@app.get("/api/health/ai")
def api_health_ai():
    status = get_active_provider_status()
    validation = Config.validate_configuration()
    return jsonify({
        "status": status,
        "validation": validation,
        "is_online_ready": validation["any_provider_configured"]
    })

# ==============================================================================
# APPLICATION ENTRYPOINT
# ==============================================================================

if __name__ == "__main__":
    validation = Config.validate_configuration()
    print("=" * 65)
    print("  GEN AI PLATFORM FOR AUTOMATED CONTENT TRANSFORMATION")
    print(f"  Web Server: http://{Config.HOST}:{Config.PORT}")
    print(f"  MongoDB Status: {'Connected' if db.is_connected else 'Offline (Using Local Storage)'}")
    print(f"  Gemini Configured: {'YES' if validation['gemini_configured'] else 'NO (Set GEMINI_API_KEY)'}")
    print(f"  OpenAI Configured: {'YES' if validation['openai_configured'] else 'NO (Set OPENAI_API_KEY)'}")
    if not validation["any_provider_configured"]:
        print("  [IMPORTANT NOTICE] Online AI Mode is ACTIVE, but neither GEMINI_API_KEY")
        print("  nor OPENAI_API_KEY is configured in your .env file.")
        print("  Transformations will prompt users to configure their API key.")
    print("=" * 65)
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
