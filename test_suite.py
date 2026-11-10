import sys
import os
import json

# Ensure project root is on sys.path dynamically
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

os.chdir(PROJECT_DIR)

from app import app
from backend.db import db

def run_tests():
    print("=" * 60)
    print("  RUNNING COMPREHENSIVE AUTOMATED TESTS")
    print("=" * 60)
    
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    client = app.test_client()
    
    results = []

    def log_test(name, success, detail=""):
        status = "PASS" if success else "FAIL"
        results.append((name, success, detail))
        print(f"[{status}] {name}: {detail}")

    # 1. Test Unauthenticated Public Routes
    res = client.get("/")
    log_test("GET / (Home Landing Page)", res.status_code == 200, f"Status {res.status_code}")

    res = client.get("/login")
    log_test("GET /login (Sign In Page)", res.status_code == 200, f"Status {res.status_code}")

    res = client.get("/register")
    log_test("GET /register (Registration Page)", res.status_code == 200, f"Status {res.status_code}")

    res = client.get("/api/health")
    data = res.get_json()
    log_test("GET /api/health", res.status_code == 200 and "storage_mode" in data, f"Storage: {data.get('storage_mode')}, AI: {data.get('primary_provider')}")

    # 2. Test User Registration
    import uuid
    test_email = f"testuser_{uuid.uuid4().hex[:6]}@example.com"
    test_password = "SecurePassword123"
    res = client.post("/register", data={
        "name": "Test User",
        "email": test_email,
        "password": test_password,
        "confirm_password": test_password
    }, follow_redirects=True)
    log_test("POST /register (Create Account)", res.status_code == 200 and b"Welcome back" in res.data, "Account created & redirected to dashboard")

    # 3. Test Protected Routes (Now Authenticated in Session)
    res = client.get("/dashboard")
    log_test("GET /dashboard", res.status_code == 200 and b"Dashboard" in res.data, "Dashboard rendered successfully")

    res = client.get("/studio")
    log_test("GET /studio", res.status_code == 200 and b"AI Content Studio" in res.data, "Studio rendered successfully")

    res = client.get("/summarizer")
    log_test("GET /summarizer", res.status_code == 200 and b"Text Summarizer" in res.data, "Summarizer rendered successfully")

    res = client.get("/paraphraser")
    log_test("GET /paraphraser", res.status_code == 200 and b"Text Paraphraser" in res.data, "Paraphraser rendered successfully")

    res = client.get("/tone")
    log_test("GET /tone", res.status_code == 200 and b"Tone Transformer" in res.data, "Tone Transformer rendered successfully")

    res = client.get("/grammar")
    log_test("GET /grammar", res.status_code == 200 and b"Grammar" in res.data, "Grammar tool rendered successfully")

    res = client.get("/history")
    log_test("GET /history", res.status_code == 200 and b"Transformation History" in res.data, "History page rendered successfully")

    # 4. Test Content Transformation API
    sample_text = (
        "Artificial Intelligence is transforming business operations across global industries. "
        "Companies are adopting large language models to automate repetitive workflows, summarize lengthy reports, "
        "and generate personalized marketing content. However, organizations must ensure proper governance, data privacy, "
        "and factual verification to maximize return on investment."
    )
    res = client.post("/api/transform", data={
        "source_text": sample_text,
        "output_format": "Executive Summary",
        "audience": "Business professionals",
        "tone": "Professional",
        "detail": "Medium",
        "provider": "auto"
    })
    t_data = res.get_json()
    created_id = t_data.get("id")
    log_test("POST /api/transform", res.status_code == 200 and "output" in t_data, f"Engine: {t_data.get('engine')}, Words out: {t_data.get('words_output')}")

    # 5. Test Dedicated Tool Endpoints
    res = client.post("/api/summarize", data={
        "source_text": sample_text,
        "summary_type": "Executive Summary",
        "detail": "Medium"
    })
    s_data = res.get_json()
    log_test("POST /api/summarize", res.status_code == 200 and "output" in s_data, f"Summary produced via {s_data.get('engine')}")

    res = client.post("/api/paraphrase", data={
        "source_text": sample_text,
        "style": "Fluent & Elegant"
    })
    p_data = res.get_json()
    log_test("POST /api/paraphrase", res.status_code == 200 and "output" in p_data, f"Paraphrase produced via {p_data.get('engine')}")

    res = client.post("/api/tone", data={
        "source_text": sample_text,
        "tone": "Executive",
        "audience": "Leadership"
    })
    tone_data = res.get_json()
    log_test("POST /api/tone", res.status_code == 200 and "output" in tone_data, f"Tone shifted via {tone_data.get('engine')}")

    res = client.post("/api/grammar", data={
        "source_text": "Artificial Inteligence are transforming buisness operations and i need to test this."
    })
    g_data = res.get_json()
    log_test("POST /api/grammar", res.status_code == 200 and "output" in g_data, f"Grammar corrected via {g_data.get('engine')}")

    # 6. Test History API
    res = client.get("/api/history")
    h_data = res.get_json()
    items = h_data.get("items", [])
    log_test("GET /api/history", res.status_code == 200 and len(items) > 0, f"{len(items)} history items found")

    if created_id:
        res = client.get(f"/api/history/{created_id}")
        log_test(f"GET /api/history/{created_id}", res.status_code == 200, "Retrieved single history record")

        res = client.delete(f"/api/history/{created_id}")
        log_test(f"DELETE /api/history/{created_id}", res.status_code == 200, "Deleted history record")

    # 7. Test Export Endpoints
    test_content = "### Executive Overview\n\n- Point 1: Key finding\n- Point 2: Strategic recommendation\n\nConclusion is solid."
    
    # TXT Export
    res = client.post("/api/export", json={"content": test_content, "type": "txt", "title": "Test Brief"})
    log_test("POST /api/export (TXT)", res.status_code == 200 and res.content_type.startswith("text/plain"), f"Size: {len(res.data)} bytes")

    # DOCX Export
    res = client.post("/api/export", json={"content": test_content, "type": "docx", "title": "Test Word Doc"})
    log_test("POST /api/export (DOCX)", res.status_code == 200 and "openxmlformats" in res.content_type, f"Size: {len(res.data)} bytes")

    # PDF Export
    res = client.post("/api/export", json={"content": test_content, "type": "pdf", "title": "Test PDF Doc"})
    log_test("POST /api/export (PDF)", res.status_code == 200, f"Type: {res.content_type}, Size: {len(res.data)} bytes")

    # PPTX Export
    res = client.post("/api/export", json={"content": test_content, "type": "pptx", "title": "Test Slide Deck"})
    log_test("POST /api/export (PPTX)", res.status_code == 200, f"Type: {res.content_type}, Size: {len(res.data)} bytes")

    # 8. Test Login Explicitly
    client.get("/logout")  # Ensure logged out first
    res = client.post("/login", data={
        "email": test_email,
        "password": "WrongPassword!"
    })
    log_test("POST /login (Invalid Password)", res.status_code == 200 and b"Invalid email or password" in res.data, "Correctly rejected invalid password")

    res = client.post("/login", data={
        "email": test_email,
        "password": test_password
    }, follow_redirects=True)
    log_test("POST /login (Valid Credentials)", res.status_code == 200 and b"Dashboard" in res.data, "Successfully logged in and reached dashboard")

    # 9. Test Document Upload Extraction (.txt)
    from io import BytesIO
    fake_txt_file = (BytesIO(b"This is an uploaded document about cloud computing and generative AI architectures."), "sample_upload.txt")
    res = client.post("/api/transform", data={
        "file": fake_txt_file,
        "output_format": "Key Takeaways"
    })
    upload_data = res.get_json()
    log_test("POST /api/transform (Uploaded File)", res.status_code == 200 and "output" in upload_data, "Document parsed and transformed successfully")

    # 10. Test Logout
    res = client.get("/logout", follow_redirects=True)
    log_test("GET /logout", res.status_code == 200 and b"signed out" in res.data, "Session cleared successfully")

    print("=" * 60)
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"TEST SUMMARY: {passed} / {total} Passed ({'100%' if passed == total else 'FAIL'})")
    print("=" * 60)
    return passed == total

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
