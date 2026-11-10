# Gen AI Platform for Automated Content Transformation

A production-ready full-stack Generative AI application designed for automated content ingestion, transformation, summarization, paraphrasing, tone shifting, grammar correction, and multi-format deliverable export.

---

## 🌟 Key Features

1. **User Authentication & Private Workspaces**:
   - Secure account registration and login with encrypted password hashing (Werkzeug).
   - Session-based protection for dashboard and tools.

2. **Executive Analytics Dashboard**:
   - Real-time transformation metrics (words processed, outputs saved, format breakdowns).
   - Live system health indicators (MongoDB status, AI provider status).
   - Quick launchpad tiles for all transformation studios.

3. **Multi-Format AI Content Studio**:
   - Ingestion of raw text or documents (.TXT, .PDF, .DOCX up to 15 MB).
   - Formats: Executive Summaries, Blog Posts, Business Reports, Presentation Slide Decks, Social Media Campaigns, FAQ Guides, Advisory Bulletins, and Key Takeaways.
   - Granular customization: Target Audience, Tone of Voice, and Detail Level.

4. **Dedicated Text Summarizer**:
   - High-impact compression: Executive Summary, Prioritized Bullet Points, TL;DR, and Comprehensive Section Summaries.

5. **Intelligent Text Paraphraser**:
   - Rephrasing styles: Standard, Fluent & Elegant, Creative, Simplified Plain English, and Academic.

6. **Adaptive Tone Transformer**:
   - Re-voice content to Professional, Formal, Casual & Friendly, Persuasive, Executive, or Technical tones.

7. **Grammar & Clarity Corrector**:
   - Automated detection and correction of grammatical mistakes, spelling typos, and syntax flaws with itemized improvement notes.

8. **Transformation History & Management**:
   - Persistent history with PyMongo (MongoDB) and resilient local JSON fallback.
   - Filter, inspect previous outputs, view full preview in modals, or delete records.

9. **1-Click Copy & Multi-Format Export**:
   - Instant clipboard copying with visual toast notifications.
   - Direct export to Plain Text (`.txt`), Microsoft Word (`.docx`), PDF Document (`.pdf`), and PowerPoint Presentations (`.pptx`).

10. **Dual AI Provider Architecture**:
    - Supports Google Gemini API (`gemini-2.5-flash` / `gemini-1.5-flash`).
    - Supports OpenAI API (`gpt-4o-mini`).
    - Built-in offline intelligent fallback engine so the platform can run immediately even without external API credentials.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.10+, Flask 3.x, Werkzeug, python-dotenv
- **Frontend**: HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3, Bootstrap Icons
- **Database**: MongoDB (PyMongo 4.x) with automatic local storage fallback
- **AI Integrations**: Google GenAI SDK (`google-genai`), OpenAI SDK (`openai`)
- **Document Processing**: PyPDF (`pypdf`), Python-Docx (`docx`), ReportLab (`reportlab`), Python-PPTX (`pptx`)
- **Deployment**: Windows 10 & 11 batch automations (`setup.bat`, `run.bat`)

---

## 🚀 Windows Quick Start

### Step 1: Automated Setup
Double-click `setup.bat` (or open Command Prompt in the project folder and execute):
```cmd
setup.bat
```
This script will:
- Check for Python 3.10+ installation.
- Automatically create a virtual environment (`venv`).
- Upgrade pip and install all required packages.
- Initialize your `.env` configuration file from `.env.example`.

### Step 2: Configure Environment (.env)
Open the newly created `.env` file in Notepad:
```cmd
notepad .env
```
Paste your **Google Gemini API Key** (obtain free at https://aistudio.google.com/app/apikey) or **OpenAI API Key**:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
MONGO_URI=mongodb://localhost:27017/
MONGO_DB=genai_content_transformation
SECRET_KEY=your_random_secret_string
```
Save and close Notepad.

### Step 3: Run the Application
Double-click `run.bat` (or run in CMD):
```cmd
run.bat
```
The application will launch at:
👉 **http://127.0.0.1:5000**

Open this address in Google Chrome, Microsoft Edge, or your preferred browser.

---

## 📁 Project Architecture

```
GenAI_Content_Transformation/
├── app.py                      # Core Flask web server & REST API
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
├── README.md                   # Project overview & documentation
├── setup.bat                   # 1-click Windows setup script
├── run.bat                     # 1-click Windows startup script
├── .gitignore                  # Git ignore rules
├── EXECUTION_GUIDE.txt         # Beginner-friendly step-by-step guide
├── templates/                  # Bootstrap 5 HTML Jinja2 templates
│   ├── base.html               # Main application layout & navbar
│   ├── index.html              # Landing / hero page
│   ├── login.html              # User login page
│   ├── register.html           # User registration page
│   ├── dashboard.html          # Analytics & metrics dashboard
│   ├── studio.html             # Multi-format AI Content Studio
│   ├── summarizer.html         # Dedicated Text Summarizer
│   ├── paraphraser.html        # Dedicated Text Paraphraser
│   ├── tone.html               # Dedicated Tone Transformer
│   ├── grammar.html            # Dedicated Grammar Corrector
│   └── history.html            # Transformation history manager
├── static/                     # Static styling and JavaScript
│   ├── css/
│   │   └── custom.css          # Dark aesthetic styling
│   └── js/
│       └── main.js             # Client-side async logic & clipboard
├── backend/                    # Modular services
│   ├── __init__.py
│   ├── auth.py                 # Password hashing & session logic
│   ├── db.py                   # MongoDB client with JSON fallback
│   ├── ai_service.py           # Gemini, OpenAI & offline engine
│   ├── document_parser.py      # PDF, DOCX, TXT document parser
│   └── exporters.py            # PDF, DOCX, PPTX, TXT generators
├── data/                       # Local database storage directory
└── frontend/                   # React + Vite source code (optional)
```

---

## 🔧 Troubleshooting

1. **'python' is not recognized as an internal or external command**:
   - Re-install Python and ensure you check **"Add Python to PATH"** in the installer.
2. **Port 5000 is already in use**:
   - Close any other running Flask application or change the port in `app.py` line `app.run(port=5001)`.
3. **MongoDB is offline**:
   - The platform will automatically run using its built-in local JSON database engine without crashing. To start the Windows MongoDB service:
     ```cmd
     net start MongoDB
     ```
4. **AI Generation Errors / Quotas**:
   - Check that your `GEMINI_API_KEY` or `OPENAI_API_KEY` is entered correctly in `.env` without surrounding spaces or quotes.
