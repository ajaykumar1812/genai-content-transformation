@echo off
setlocal

echo ============================================================
echo   GEN AI PLATFORM FOR AUTOMATED CONTENT TRANSFORMATION
echo ============================================================
echo.

:: 1. Check & Activate virtual environment
if not exist "venv\Scripts\activate.bat" goto :no_venv

echo [1/3] Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)
echo   Virtual environment activated: (venv)
echo.

:: 2. Check dependencies
echo [2/3] Verifying core dependencies...
python -c "import flask, dotenv, pymongo, werkzeug" >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Core dependencies are missing or incomplete.
    echo Installing dependencies from requirements.txt...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Dependency installation failed.
        pause
        exit /b 1
    )
)
echo   Dependencies verified.
echo.

:: 3. Launch Flask application
echo [3/3] Starting Gen AI Platform...
echo.
echo ============================================================
echo   APPLICATION RUNNING AT:
echo   http://127.0.0.1:5000
echo ============================================================
echo.
echo Open your web browser and visit:
echo.
echo   http://127.0.0.1:5000
echo.
echo [NOTE] Press CTRL+C in this command window to stop the server.
echo ============================================================
echo.

python app.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] The application stopped unexpectedly.
    echo Possible causes:
    echo  - Port 5000 is already in use by another application.
    echo  - Missing packages or invalid syntax in Python files.
    echo.
    pause
)
goto :eof

:no_venv
echo [ERROR] Virtual environment 'venv' was not found!
echo Please run 'setup.bat' first to set up the application environment.
echo.
pause
exit /b 1
