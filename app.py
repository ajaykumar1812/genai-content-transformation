import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, jsonify, send_file
)

# Load environment configuration
load_dotenv()

from backend.db import db
from backend.auth import hash_password, verify_password, login_required, get_current_user
from backend.document_parser import extract_document_text
from backend.ai_service import (
    transform_content, summarize_text, paraphrase_text,
    transform_tone, correct_grammar, get_active_provider_status
)
from backend.exporters import export_as_txt, export_as_docx, export_as_pdf, export_as_pptx

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "genai-content-transformation-secure-secret-key-2026")
app.config["MAX_CONTENT_LENGTH"] = 15 * 1024 * 1024  # 15 MB max file upload

@app.context_processor
def inject_global_data():
    user = get_current_user()
    health = get_active_provider_status()
    health["mongodb_connected"] = db.is_connected
    return {
        "current_user": user,
        "system_status": health,
        "now": datetime.now()
    }

# ==========================================
# WEB UI ROUTES
# ==========================================

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
        user = db.get_user_by_email(email)
        if not user or not verify_password(user["password_hash"], password):
            flash("Invalid email or password. Please try again.", "danger")
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
        
        if not name or not email or not password:
            flash("All fields are required.", "warning")
            return render_template("register.html", name=name, email=email)
        if len(password) < 6:
            flash("Password must be at least 6 characters.", "warning")
            return render_template("register.html", name=name, email=email)
        if password != confirm:
            flash("Passwords do not match.", "warning")
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
            flash(f"Registration error: {e}", "danger")
            
    return render_template("register.html")

@app.get("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("login"))

@app.get("/dashboard")
@login_required
def dashboard():
    stats = db.get_dashboard_stats(session.get("user_id"))
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

@app.get("/history")
@login_required
def history():
    items = db.get_user_history(session.get("user_id"), limit=100)
    return render_template("history.html", items=items)

# ==========================================
# ASYNC API ROUTES
# ==========================================

@app.post("/api/transform")
def api_transform():
    user_id = session.get("user_id")
    try:
        source_text = (request.form.get("source_text") or "").strip()
        uploaded_file = request.files.get("file")
        if uploaded_file and uploaded_file.filename:
            source_text = extract_document_text(uploaded_file).strip()
            
        if not source_text:
            return jsonify({"error": "Please provide input text or upload a document."}), 400
            
        output_format = request.form.get("output_format", "Executive Summary")
        audience = request.form.get("audience", "General audience")
        tone_val = request.form.get("tone", "Professional")
        detail = request.form.get("detail", "Medium")
        provider = request.form.get("provider", "auto")
        
        output, engine = transform_content(
            source=source_text,
            output_format=output_format,
            audience=audience,
            tone=tone_val,
            detail=detail,
            provider=provider
        )
        
        saved_record = db.save_transformation(
            user_id=user_id,
            source=source_text,
            output=output,
            format_type=output_format,
            audience=audience,
            tone=tone_val,
            detail=detail,
            title=f"{output_format} Transformation"
        )
        
        return jsonify({
            "output": output,
            "engine": engine,
            "format": output_format,
            "id": saved_record.get("id"),
            "words_input": len(source_text.split()),
            "words_output": len(output.split())
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.post("/api/summarize")
def api_summarize():
    user_id = session.get("user_id")
    try:
        source_text = (request.form.get("source_text") or "").strip()
        uploaded_file = request.files.get("file")
        if uploaded_file and uploaded_file.filename:
            source_text = extract_document_text(uploaded_file).strip()
            
        if not source_text:
            return jsonify({"error": "Please provide input text or upload a document."}), 400
            
        summary_type = request.form.get("summary_type", "Executive Summary")
        detail = request.form.get("detail", "Medium")
        provider = request.form.get("provider", "auto")
        
        output, engine = summarize_text(source_text, summary_type, detail, provider)
        saved = db.save_transformation(
            user_id=user_id,
            source=source_text,
            output=output,
            format_type=f"Summary: {summary_type}",
            audience="General",
            tone="Analytical",
            detail=detail,
            title=f"Summary ({summary_type})"
        )
        return jsonify({
            "output": output,
            "engine": engine,
            "id": saved.get("id"),
            "words_input": len(source_text.split()),
            "words_output": len(output.split())
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.post("/api/paraphrase")
def api_paraphrase():
    user_id = session.get("user_id")
    try:
        source_text = (request.form.get("source_text") or "").strip()
        uploaded_file = request.files.get("file")
        if uploaded_file and uploaded_file.filename:
            source_text = extract_document_text(uploaded_file).strip()
            
        if not source_text:
            return jsonify({"error": "Please provide text to paraphrase."}), 400
            
        style = request.form.get("style", "Standard")
        provider = request.form.get("provider", "auto")
        
        output, engine = paraphrase_text(source_text, style, provider)
        saved = db.save_transformation(
            user_id=user_id,
            source=source_text,
            output=output,
            format_type=f"Paraphrase: {style}",
            audience="General",
            tone=style,
            title=f"Paraphrase ({style})"
        )
        return jsonify({
            "output": output,
            "engine": engine,
            "id": saved.get("id"),
            "words_input": len(source_text.split()),
            "words_output": len(output.split())
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.post("/api/tone")
def api_tone():
    user_id = session.get("user_id")
    try:
        source_text = (request.form.get("source_text") or "").strip()
        uploaded_file = request.files.get("file")
        if uploaded_file and uploaded_file.filename:
            source_text = extract_document_text(uploaded_file).strip()
            
        if not source_text:
            return jsonify({"error": "Please provide text for tone transformation."}), 400
            
        target_tone = request.form.get("tone", "Professional")
        audience = request.form.get("audience", "General audience")
        provider = request.form.get("provider", "auto")
        
        output, engine = transform_tone(source_text, target_tone, audience, provider)
        saved = db.save_transformation(
            user_id=user_id,
            source=source_text,
            output=output,
            format_type=f"Tone: {target_tone}",
            audience=audience,
            tone=target_tone,
            title=f"Tone Shift ({target_tone})"
        )
        return jsonify({
            "output": output,
            "engine": engine,
            "id": saved.get("id"),
            "words_input": len(source_text.split()),
            "words_output": len(output.split())
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.post("/api/grammar")
def api_grammar():
    user_id = session.get("user_id")
    try:
        source_text = (request.form.get("source_text") or "").strip()
        uploaded_file = request.files.get("file")
        if uploaded_file and uploaded_file.filename:
            source_text = extract_document_text(uploaded_file).strip()
            
        if not source_text:
            return jsonify({"error": "Please provide text to correct."}), 400
            
        provider = request.form.get("provider", "auto")
        output, engine = correct_grammar(source_text, provider=provider)
        saved = db.save_transformation(
            user_id=user_id,
            source=source_text,
            output=output,
            format_type="Grammar Correction",
            audience="General",
            tone="Corrected",
            title="Grammar & Clarity Fix"
        )
        return jsonify({
            "output": output,
            "engine": engine,
            "id": saved.get("id"),
            "words_input": len(source_text.split()),
            "words_output": len(output.split())
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.get("/api/history")
def api_history():
    user_id = session.get("user_id")
    items = db.get_user_history(user_id=user_id, limit=50)
    return jsonify({"items": items})

@app.get("/api/history/<item_id>")
def api_history_item(item_id):
    user_id = session.get("user_id")
    item = db.get_transformation_by_id(item_id, user_id=user_id)
    if not item:
        return jsonify({"error": "Record not found."}), 404
    return jsonify({"item": item})

@app.delete("/api/history/<item_id>")
def api_delete_history(item_id):
    user_id = session.get("user_id")
    success = db.delete_transformation(item_id, user_id=user_id)
    if not success:
        return jsonify({"error": "Failed to delete record or record not found."}), 404
    return jsonify({"success": True})

@app.post("/api/history/clear")
def api_clear_history():
    user_id = session.get("user_id")
    db.clear_user_history(user_id)
    return jsonify({"success": True})

@app.post("/api/export")
def api_export():
    data = request.get_json(silent=True) or {}
    content = (data.get("content") or request.form.get("content") or "").strip()
    fmt = (data.get("type") or request.form.get("type") or "txt").lower()
    title = (data.get("title") or request.form.get("title") or "Gen AI Content Transformation").strip()
    
    if not content:
        return jsonify({"error": "No content available to export."}), 400
        
    if fmt == "docx":
        buffer, mimetype, filename = export_as_docx(title, content)
    elif fmt == "pdf":
        buffer, mimetype, filename = export_as_pdf(title, content)
    elif fmt == "pptx":
        buffer, mimetype, filename = export_as_pptx(title, content)
    else:
        buffer, mimetype, filename = export_as_txt(content)
        
    return send_file(
        buffer,
        mimetype=mimetype,
        as_attachment=True,
        download_name=filename
    )

@app.get("/api/health")
def api_health():
    status = get_active_provider_status()
    status["mongodb"] = db.is_connected
    status["storage_mode"] = "MongoDB" if db.is_connected else "Local Storage"
    return jsonify(status)

# ==========================================
# APPLICATION STARTUP
# ==========================================

if __name__ == "__main__":
    print("=" * 60)
    print("  GEN AI PLATFORM FOR AUTOMATED CONTENT TRANSFORMATION")
    print("  Running at: http://127.0.0.1:5000")
    print("  Press CTRL+C in this console to stop the server.")
    print("=" * 60)
    app.run(host="127.0.0.1", port=5000, debug=True)
