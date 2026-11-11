# Gen AI Platform for Automated Content Transformation

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Framework-Flask%203.x-green.svg)](https://flask.palletsprojects.com/)
[![AI Providers](https://img.shields.io/badge/AI%20Engines-Google%20Gemini%20%7C%20OpenAI%20GPT-purple.svg)](https://aistudio.google.com/)
[![Database](https://img.shields.io/badge/Database-MongoDB%20Atlas%20%7C%20PyMongo-emerald.svg)](https://www.mongodb.com/cloud/atlas)
[![License](https://img.shields.io/badge/Project-B.Tech%20CSE%20Capstone-orange.svg)](#)

A professional, enterprise-grade, online AI-powered web platform for automated document ingestion, multi-modal content restructuring, summarization, paraphrasing, tone shifting, grammar correction, and multi-format document exporting.

---

## 📑 Table of Contents

1. [Project Overview](#-project-overview)
2. [Problem Statement & Objectives](#-problem-statement--objectives)
3. [Key Features & Capabilities](#-key-features--capabilities)
4. [Technology Stack](#-technology-stack)
5. [System Architecture](#-system-architecture)
6. [Project Structure](#-project-structure)
7. [Local Installation & Setup (Windows / Linux / macOS)](#-local-installation--setup)
8. [Environment Configuration & API Keys](#-environment-configuration--api-keys)
9. [MongoDB Atlas Setup Guide](#-mongodb-atlas-setup-guide)
10. [AI Provider Setup Guides](#-ai-provider-setup-guides)
    - [Google Gemini API Setup](#google-gemini-api-setup)
    - [OpenAI API Setup](#openai-api-setup)
11. [Running the Application](#-running-the-application)
12. [Automated Testing Suite](#-automated-testing-suite)
13. [Deployment to Render](#-deployment-to-render)
14. [GitHub Repository Setup](#-github-repository-setup)
15. [Security & Privacy](#-security--privacy)
16. [Future Enhancements](#-future-enhancements)

---

## 🌟 Project Overview

The **Gen AI Platform for Automated Content Transformation** is a cloud-ready SaaS application engineered to address information overload and communication friction in enterprise environments. By integrating official SDKs from **Google Gemini** and **OpenAI**, the platform empowers users to ingest complex unstructured documents (PDF, DOCX, TXT) and instantly synthesize, rewrite, and tailor them into actionable business deliverables.

### Strict Online AI Mode
The platform operates exclusively in **Online AI Mode**:
- **No hardcoded responses or dummy simulations.**
- **No silent fallbacks to offline string manipulation.**
- All transformations invoke official **OpenAI** or **Google Gemini** endpoints.
- Granular error diagnostics clearly classify:
  - Missing or Invalid API Credentials (`401 AuthenticationError`)
  - Quota / Rate-limit Exhaustion (`429 QuotaError`)
  - Network Timeouts & Disconnections (`503 NetworkError`)
  - Invalid Model Specifications (`404 ModelError`)
  - Empty or Malformed Input Data (`400 InvalidInput`)

---

## 🎯 Problem Statement & Objectives

### Problem Statement
In contemporary academic, corporate, and research settings, knowledge workers spend up to 40% of their working hours manually summarizing lengthy reports, translating complex jargon into executive briefs, rewriting text for different audiences, and reformatting content for diverse channels (slides, blogs, emails, social media). Existing consumer tools either offer fragmented utility, rely on insecure pastebins, or obscure errors with opaque failure modes.

### Core Objectives
1. **Unified Enterprise AI Workspace**: Centralize multi-format content transformation into a single modern dashboard.
2. **Dual-Provider Architecture**: Offer dynamic switching between Google Gemini and OpenAI GPT models with zero downtime or vendor lock-in.
3. **Automated Document Parsing**: Ingest multi-page PDFs, Microsoft Word documents, and text files with intelligent header/footer removal, artifact cleaning, and scanned image detection.
4. **Multi-Format Deliverable Exporting**: Export generated content directly to `.docx`, `.pdf`, `.pptx`, and `.txt`.
5. **Strict Data Isolation & Security**: Ensure user-specific history isolation, password hashing, environment secret protection, and rate limiting.

---

## ⚡ Key Features & Capabilities

### 1. AI Content Studio
- **Dual-Panel Workspace**: Side-by-side view featuring real-time input configuration on the left and rendered Markdown on the right.
- **Provider & Model Selector**: Choose dynamically between Google Gemini (`gemini-3.6-flash` ✅, `gemini-3.5-flash` ✅, `gemini-3.8-flash` ⚠️ 20 req/day Free Tier) and OpenAI (`gpt-4o-mini`, `gpt-4o`).
- **Dynamic Deliverable Types**:
  - Executive Summaries
  - High-Conversion SEO Blog Posts (with Meta Description and Keywords)
  - Formal Corporate Business Reports
  - Presentation Slide Decks (with bullet points and slide headings)
  - Frequently Asked Questions (FAQ Guides)
  - Key Strategic Takeaways
  - Social Media Campaigns (LinkedIn, Twitter/X, Instagram, Facebook)

### 2. Specialized Transformation Tools
- **AI Summarizer**: 5 distinct compression styles (Short, Medium, Detailed, Prioritized Bullet-points, Executive Brief).
- **AI Paraphraser**: 5 stylistic rewrites (Standard, Professional, Academic, Simple English, Creative).
- **Grammar & Style Corrector**: Three-part breakdown displaying Corrected Text, Key Corrections Made, and Structural Improvements.
- **Tone Transformer**: 9 emotional and professional altitudes (Professional, Formal, Casual, Academic, Persuasive, Friendly, Confident, Business, Creative).

### 3. Document Processing Hub
- Ingest `.pdf`, `.docx`, and `.txt` up to 15 MB.
- Detects repeated headers/footers appearing across 40%+ of pages and strips them.
- Removes standalone page numbers and layout artifacts while preserving section headings.
- Scanned PDF detection: Flags image-only PDFs that require Optical Character Recognition (OCR).
- Immediate text preview with word and character count before transformation.

### 4. Transformation History & Persistence
- User-isolated storage backed by **MongoDB Atlas** with seamless local fallback for offline dev.
- Real-time keyword search across title, source, and generated output.
- Filter by deliverable type (Summary, Blog, Report, Deck, Tone, etc.).
- Modal preview with Markdown rendering, clipboard copy, and one-click TXT download.
- Individual deletion and confirmed "Clear All History" operations.

### 5. Multi-Format Exporters
- **Plain Text (`.txt`)**: Clean UTF-8 encoded text with deliverable headers.
- **Word Document (`.docx`)**: Formatted headings (H1/H2/H3), bullet points, and metadata styling using `python-docx`.
- **PDF Document (`.pdf`)**: Styled publication-ready PDF using `reportlab`.
- **PowerPoint Presentation (`.pptx`)**: Generates slide decks with slide titles and bullet points using `python-pptx`.

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3, Bootstrap Icons, Marked.js |
| **Backend Framework** | Python 3.11+, Flask 3.x, Werkzeug 3.x, Gunicorn (Production WSGI) |
| **AI Integration** | Official `google-genai` SDK 3.x, Official `openai` SDK 3.x |
| **Database** | MongoDB Atlas Cloud, PyMongo 4.x, dnspython, certifi |
| **Document Processing** | PyPDF 7.x, python-docx 1.2.x |
| **Export Engines** | ReportLab 5.x, python-docx 1.2.x, python-pptx 1.0.x |
| **Security** | Scrypt Password Hashing, HTTP-only SameSite Cookies, Sliding Rate Limiting |
| **Deployment** | Render, GitHub, MongoDB Atlas |

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    subgraph Client["Frontend Layer (Client Browser)"]
        UI["Bootstrap 5 + JS UI\n(Studio, Tools, Hub, History)"]
        Markdown["Marked.js Markdown Parser"]
        Theme["Theme Switcher (Dark / Light)"]
    end

    subgraph Backend["Flask REST API Server"]
        Router["Route Dispatcher (app.py)"]
        Auth["Auth Controller (backend/auth.py)"]
        DocParser["Document Parser (backend/document_parser.py)"]
        Validators["Input Validation (backend/validators.py)"]
        AIService["AI Orchestrator (backend/ai_service.py)"]
        Exporters["Export Engines (backend/exporters.py)"]
    end

    subgraph External["External Cloud Services"]
        Gemini["Google Gemini API\n(gemini-3.6-flash / 3.5-flash)"]
        OpenAI["OpenAI API\n(gpt-4o-mini / gpt-4o)"]
        Atlas[("MongoDB Atlas Cloud\n(Users, History, Settings)")]
    end

    UI --> Router
    Router --> Auth
    Router --> Validators
    Router --> DocParser
    Router --> AIService
    Router --> Exporters

    AIService -->|Official GenAI SDK| Gemini
    AIService -->|Official OpenAI SDK| OpenAI
    Auth --> Atlas
    AIService -.->|Save Record| Atlas
```

---

## 📁 Project Structure

```
GenAI_Content_Transformation/
│
├── app.py                     # Main Flask web application & REST API routes
├── config.py                  # Central configuration & environment loader
├── requirements.txt           # Production pinned Python dependencies
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules (secrets, venv, cache)
├── README.md                  # Comprehensive documentation
├── render.yaml                # Render Blueprint infrastructure-as-code
├── Procfile                   # Process file for cloud web services
├── setup.bat                  # Automated 1-click Windows setup script
├── run.bat                    # Automated 1-click Windows run script
├── test_document.pdf          # Sample enterprise document for testing
├── test_suite.py              # Automated 30-scenario test runner & reporter
│
├── backend/                   # Modular backend service layer
│   ├── __init__.py            # Package initialization
│   ├── ai_service.py          # Unified AI orchestrator & prompt templates
│   ├── openai_service.py      # Official OpenAI SDK integration wrapper
│   ├── gemini_service.py      # Official Google Gen AI SDK integration wrapper
│   ├── document_parser.py     # PDF, DOCX, TXT parser & artifact cleaner
│   ├── db.py                  # MongoDB Atlas database manager & fallback
│   ├── auth.py                # Authentication, password hashing & decorators
│   ├── exporters.py           # Multi-format exports (TXT, DOCX, PDF, PPTX)
│   └── validators.py          # Input sanitization & security validators
│
├── templates/                 # Jinja2 HTML5 Bootstrap 5 templates
│   ├── base.html              # Base layout with theme toggle, nav & footer
│   ├── index.html             # Landing page
│   ├── login.html             # Sign in page
│   ├── register.html          # Registration page
│   ├── dashboard.html         # User workspace & statistics dashboard
│   ├── studio.html            # AI Content Studio (dual-panel workspace)
│   ├── summarizer.html        # AI Summarizer tool
│   ├── paraphraser.html       # AI Paraphraser tool
│   ├── grammar.html           # Grammar & style corrector tool
│   ├── tone.html              # Tone transformer tool
│   ├── documents.html         # Document Hub (upload, parse, preview)
│   ├── history.html           # Transformation history & search
│   └── settings.html          # User profile, preferences & API monitor
│
├── static/                    # Static frontend assets
│   ├── css/
│   │   └── custom.css         # Custom SaaS stylesheet (Dark/Light theme)
│   └── js/
│       └── main.js            # Interactive logic, theme toggle & exports
│
└── tests/                     # Modular automated test suite
    ├── __init__.py            # Test package
    ├── test_auth.py           # Authentication & route protection tests
    ├── test_ai_service.py     # AI transformation engines & providers tests
    ├── test_documents.py      # Document ingestion & format validation tests
    ├── test_history.py        # History CRUD & user isolation tests
    ├── test_exports.py        # Binary exporter verification tests
    └── test_api_errors.py     # Error classification & status code tests
```

---

## 💻 Local Installation & Setup

### Prerequisites
- **Operating System:** Windows 10/11, macOS, or Ubuntu/Debian Linux
- **Python:** Version 3.10, 3.11, 3.12, or 3.13 installed (`python --version`)
- **Git:** Installed for repository cloning

### Method 1: Automated Windows Setup (Fastest)

1. Open Command Prompt (`cmd`) in the project directory:
   ```cmd
   cd /d "C:\Users\hp\.gemini\antigravity\scratch\GenAI_Content_Transformation"
   ```
2. Run the automated setup script:
   ```cmd
   setup.bat
   ```
   *This automatically creates a virtual environment `venv`, upgrades pip, installs all dependencies from `requirements.txt`, and generates your `.env` configuration file.*
3. Launch the platform:
   ```cmd
   run.bat
   ```
4. Open your browser and navigate to: **`http://127.0.0.1:5000`**

---

### Method 2: Manual Setup (CMD / PowerShell / Linux / macOS)

#### Windows CMD:
```cmd
:: Create virtual environment
python -m venv venv

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

:: Copy environment template
copy .env.example .env

:: Run application
python app.py
```

#### Windows PowerShell:
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt

# Create .env file
Copy-Item .env.example .env

# Run application
python app.py
```

#### Linux / macOS Terminal:
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Run application
python3 app.py
```

---

## ⚙️ Environment Configuration & API Keys

Open the `.env` file in any text editor (`notepad .env`) and configure the following variables:

```ini
# Flask Secret Key
SECRET_KEY=replace-with-a-random-32-char-string-for-production
FLASK_DEBUG=false
HOST=0.0.0.0
PORT=5000

# MongoDB Database Configuration
MONGO_URI=mongodb://localhost:27017/
MONGO_DB=genai_content_transformation

# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.6-flash

# OpenAI API
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

---

## 🍃 MongoDB Atlas Setup Guide

For permanent cloud persistence across server restarts or Render redeployments:

1. **Create Free Account**: Visit [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register) and register.
2. **Deploy Cluster**: Select **M0 Shared (Free)** tier in your preferred AWS/GCP region.
3. **Create Database User**:
   - Go to **Security > Database Access > Add New Database User**.
   - Select **Password Authentication**.
   - Set username: `appuser`, password: `YourStrongPassword123`.
   - Set role: **Read and write to any database**.
4. **Configure Network Access**:
   - Go to **Security > Network Access > Add IP Address**.
   - Choose **Allow Access from Anywhere** (`0.0.0.0/0`).
5. **Get Connection String**:
   - Click **Connect > Drivers (Python)**.
   - Copy string:
     ```
     mongodb+srv://appuser:YourStrongPassword123@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority
     ```
   - Paste into `.env` as `MONGO_URI`.

---

## 🤖 AI Provider Setup Guides

### Google Gemini API Setup (Recommended)
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Sign in with your Google account.
3. Click **Create API Key**.
4. Copy the generated key.
5. In your `.env` file, set:
   ```ini
   GEMINI_API_KEY=AIzaSy...your_key_here
   GEMINI_MODEL=gemini-3.6-flash
   ```

> **Free Tier quota note:** `gemini-3.6-flash` and `gemini-3.5-flash` are the recommended defaults.
> `gemini-3.8-flash` shares a **20 requests/day** Free Tier bucket — if you hit the daily limit the app shows a clear error asking you to switch to `gemini-3.6-flash` or `gemini-3.5-flash`.
> Paid API plans have no such restriction.

### OpenAI API Setup
1. Go to [OpenAI Platform API Keys](https://platform.openai.com/api-keys).
2. Sign in or register your account.
3. Click **Create new secret key**.
4. Copy the secret key (`sk-proj-...`).
5. In your `.env` file, set:
   ```ini
   OPENAI_API_KEY=sk-proj-...your_key_here
   OPENAI_MODEL=gpt-4o-mini
   ```

---

## 🧪 Automated Testing Suite

The project includes an automated test suite verifying all 35 critical system scenarios:

```cmd
:: Run unified 35-scenario test runner
python test_suite.py
```

Or run modular unit tests:
```cmd
python -m unittest discover tests
```

### Verified Test Matrix (100% Pass Rate)

| # | Test Scenario | Verified Capability | Status |
| :- | :--- | :--- | :-: |
| 01 | Application Startup | HTTP 200 Landing Page loads cleanly | **PASS** |
| 02 | User Registration | Cryptographic password hashing & account creation | **PASS** |
| 03 | User Login | Valid credentials authenticated into session | **PASS** |
| 04 | User Logout | Session flushed and redirected to login | **PASS** |
| 05 | Protected Routes | Unauthenticated requests redirected / returned 401 | **PASS** |
| 06 | OpenAI Integration | Official OpenAI SDK contract execution | **PASS** |
| 07 | Gemini Integration | Official Google GenAI SDK contract execution | **PASS** |
| 08 | Provider Switching | Dynamic runtime switching between Gemini & OpenAI | **PASS** |
| 09 | AI Summarizer | 5 summary architectures (Exec, Bullets, TL;DR) | **PASS** |
| 10 | AI Paraphraser | 5 rewrite styles preserving original meaning | **PASS** |
| 11 | Grammar Correction | 3-part structured proofread and explanations | **PASS** |
| 12 | Tone Transformation | 9 distinct voice modalities tested | **PASS** |
| 13 | Blog Generation | SEO blog with title, meta description & keywords | **PASS** |
| 14 | Report Generation | Formal business report with numbered sections | **PASS** |
| 15 | Presentation Deck | Slide-wise format parsing for PPTX | **PASS** |
| 16 | PDF Upload | PyPDF text extraction & header/footer strip | **PASS** |
| 17 | DOCX Upload | python-docx paragraph extraction | **PASS** |
| 18 | TXT Upload | UTF-8 / Latin-1 text extraction | **PASS** |
| 19 | Invalid File Handling | Unsupported extensions rejected with 400 | **PASS** |
| 20 | Empty Input Handling | Empty source text rejected with 400 invalid_input | **PASS** |
| 21 | History Saving | Deliverable logged with word counts & timestamps | **PASS** |
| 22 | History Retrieval | Multi-record retrieval with search/filter | **PASS** |
| 23 | History Deletion | Individual record deletion | **PASS** |
| 24 | TXT Export | UTF-8 formatted stream generated | **PASS** |
| 25 | PDF Export | ReportLab styled PDF binary generated | **PASS** |
| 26 | DOCX Export | python-docx Word document binary generated | **PASS** |
| 27 | PPTX Export | python-pptx presentation deck generated | **PASS** |
| 28 | Unauthorized Access | User A cannot read or delete User B's records | **PASS** |
| 29 | API Failure Handling | Quota (429) & Auth (401) errors distinctly handled | **PASS** |
| 30 | Database Failure Handling | Automatic fallback to local storage on ping fail | **PASS** |
| 31 | Retry on Transient 503 | Exponential backoff retries succeed on 2nd attempt | **PASS** |
| 32 | Retry Exhaustion | All 3 attempts fail — clear error returned to caller | **PASS** |
| 33 | Daily Quota Fast-Fail | 20 req/day Free Tier limit → immediate error, no retry | **PASS** |
| 34 | Auth Error No Retry | Invalid API key → immediate 401 error, no retry | **PASS** |
| 35 | Model Not Found Error | Unavailable model → 404 error with guidance message | **PASS** |

---

## 🚀 Deployment to Render

The repository is configured for direct deployment on [Render](https://render.com) using `render.yaml` or manual Web Service creation:

### Deploying via Render Web Service
1. **Push your code to GitHub** (see next section).
2. Go to **[Render Dashboard](https://dashboard.render.com/)** and click **New + > Web Service**.
3. Connect your GitHub repository.
4. Configure service settings:
   - **Name**: `genai-content-transformation`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT app:app`
   - **Health Check Path**: `/api/health`
5. In the **Environment Variables** tab, add:
   - `SECRET_KEY`: (Generate a secure random key)
   - `FLASK_DEBUG`: `false`
   - `MONGO_URI`: (Your MongoDB Atlas connection string)
   - `MONGO_DB`: `genai_content_transformation`
   - `GEMINI_API_KEY`: (Your Google Gemini API key)
   - `GEMINI_MODEL`: `gemini-3.6-flash`
   - `OPENAI_API_KEY`: (Your OpenAI API key)
   - `OPENAI_MODEL`: `gpt-4o-mini`
6. Click **Deploy Web Service**.

---

## 🐙 GitHub Repository Setup

To push your project to a new GitHub repository:

```bash
# Initialize git repository
git init

# Add all project files
git add .

# Verify .env and sensitive data are excluded by .gitignore
git status

# Commit
git commit -m "Initial commit: Gen AI Platform for Automated Content Transformation"

# Link to GitHub remote (replace with your repo URL)
git remote add origin https://github.com/<your-username>/genai-content-transformation.git
git branch -M main
git push -u origin main
```

---

## 🔒 Security & Privacy

1. **Zero Secret Exposure**: API keys and database credentials are kept strictly in `.env` and environment variables. The `.gitignore` ensures credentials are never committed.
2. **Password Cryptography**: Passwords are hashed using Werkzeug's secure implementation (`generate_password_hash`) and never stored in plain text.
3. **Strict Data Isolation**: Every transformation record is tagged with `user_id`. Queries strictly filter by session user ID, preventing cross-tenant leakage.
4. **Input Sanitization & Rate Limiting**: All user input strings are stripped of null bytes and validated. A sliding window rate limiter prevents API abuse.
5. **No Fake Responses**: Clear error banners notify users if an API key is missing or quota is exhausted, ensuring transparency and accountability.

---

## 🔮 Future Enhancements

- **Multilingual Support**: Real-time cross-language translation into 50+ languages during transformation.
- **OCR Ingestion**: Tesseract OCR or Google Cloud Vision integration to extract text from scanned PDFs and photos.
- **Audio Transcript Processing**: Whisper API integration to transcribe audio recordings and summarize meetings.
- **Custom Template Builder**: Allow enterprises to define proprietary document output schemas and styling templates.

---

## 📜 Academic Capstone Declaration

This project was engineered as a final-year **B.Tech Computer Science and Engineering** capstone project. Designed, architected, and tested to meet modern enterprise software engineering standards.
