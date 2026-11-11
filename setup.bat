@echo off
setlocal

echo ============================================================
echo   GEN AI PLATFORM - AUTOMATED SETUP (WINDOWS 10 / 11)
echo ============================================================
echo.

:: 1. Check whether Python is installed
echo [1/6] Checking Python installation...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not found in your system PATH.
    echo Please install Python 3.10 or higher from:
    echo   https://www.python.org/downloads/
    echo Make sure to check the box: "Add python.exe to PATH"
    echo.
    pause
    exit /b 1
)

python --version
if %errorlevel% neq 0 (
    echo [ERROR] Failed to execute Python command.
    pause
    exit /b 1
)
echo.

:: 2. Create virtual environment named venv
echo [2/6] Setting up virtual environment venv...
if exist "venv\Scripts\activate.bat" goto :venv_exists

echo   Creating new virtual environment in .\venv ...
python -m venv venv
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b 1
)
echo   Virtual environment created successfully.
goto :venv_ready

:venv_exists
echo   Existing virtual environment detected.

:venv_ready
echo.

:: 3. Activate the virtual environment
echo [3/6] Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)
echo   Virtual environment activated: (venv)
echo.

:: 4. Upgrade pip inside venv
echo [4/6] Upgrading pip...
python -m pip install --upgrade pip --quiet
echo   pip is up to date.
echo.

:: 5. Install all required dependencies
echo [5/6] Installing dependencies from requirements.txt...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [WARNING] Some dependencies had warnings during installation.
)
echo   Dependencies installation completed.
echo.

:: 6. Check for .env file & provide instructions
echo [6/6] Checking environment configuration file...
if exist ".env" goto :env_exists

echo   .env not found. Creating from .env.example ...
copy .env.example .env >nul
echo.
echo   ------------------------------------------------------------
echo   [ACTION REQUIRED] A new .env configuration file was created.
echo   Please open .env in Notepad to configure your online AI credentials:
echo.
echo     notepad .env
echo.
echo   Add your GEMINI_API_KEY from https://aistudio.google.com/app/apikey
echo   or OPENAI_API_KEY from https://platform.openai.com/api-keys
echo   The platform operates in ONLINE AI MODE using official APIs.
echo   ------------------------------------------------------------
goto :setup_complete

:env_exists
echo   Existing .env file detected. Preserving your configuration.

:setup_complete
echo.
echo ============================================================
echo   SETUP COMPLETED SUCCESSFULLY!
echo   To launch the platform, run: run.bat
echo ============================================================
echo.
pause
