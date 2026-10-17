@echo off
chcp 65001 > nul
title Türkçe Ses Tanıma ^& Konuşmacı Ayrıştırma Aracı

cd /d "%~dp0"

echo ==============================================================
echo  Türkçe Ses Tanıma ^& Konuşmacı Ayrıştırma (STT + Diarization)
echo ==============================================================
echo.

if not exist "venv\Scripts\python.exe" (
    echo [UYARI] Sanal ortam bulunamadi! Lutfen once setup_env.bat dosyasini calistirin.
    echo.
    pause
    exit /b 1
)

echo Uygulama başlatılıyor, lütfen bekleyin...
echo.

.\venv\Scripts\python.exe main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [HATA] Uygulama sonlandi. Kod: %ERRORLEVEL%
    pause
)
