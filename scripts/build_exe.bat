@echo off
setlocal enabledelayedexpansion

echo ====================================================================
echo  Speech-To-Text Standalone Windows Executable Build Pipeline
echo ====================================================================

cd /d "%~dp0\.."

if exist ".\venv\Scripts\python.exe" (
    set "PYTHON_EXE=.\venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

echo [1/4] Checking Python environment...
"%PYTHON_EXE%" --version
if errorlevel 1 (
    echo [ERROR] Python environment not found. Please run run.bat first.
    exit /b 1
)

echo [2/4] Ensuring build tools (pyinstaller) are installed...
"%PYTHON_EXE%" -m pip install --upgrade pyinstaller

echo [3/4] Compiling SpeechToText.exe using SpeechToText.spec...
"%PYTHON_EXE%" -m PyInstaller --clean --noconfirm SpeechToText.spec

if not exist "dist\SpeechToText.exe" (
    echo [ERROR] Build failed. dist\SpeechToText.exe was not generated.
    exit /b 1
)

echo [4/4] Generating SHA256 checksum...
powershell -NoProfile -Command "(Get-FileHash -Algorithm SHA256 'dist\SpeechToText.exe').Hash | Out-File -Encoding utf8 'dist\SpeechToText.exe.sha256'"

echo ====================================================================
echo  Build Succeeded!
echo  Executable: dist\SpeechToText.exe
echo  Checksum  : dist\SpeechToText.exe.sha256
echo ====================================================================
