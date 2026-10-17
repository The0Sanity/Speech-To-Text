@echo off
chcp 65001 > nul
title SesMetin Pro - Turkce STT ve Konusmaci Ayrastirma

cd /d "%~dp0"

set "PY="

:: 1. Mevcut venv varsa onu kullan
if exist "venv\Scripts\python.exe" (
    set "PY=venv\Scripts\python.exe"
    goto :CHECK_DEPS
)

:: 2. Sistemde Python kontrol et
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "SYSTEM_PY=python"
    goto :SETUP_VENV
)

where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "SYSTEM_PY=py -3"
    goto :SETUP_VENV
)

echo [HATA] Sisteminizde Python bulunamadi!
echo Lutfen https://www.python.org adresinden Python kurunuz.
pause
exit /b 1

:SETUP_VENV
echo Sanal ortam hazirlaniyor...
%SYSTEM_PY% -m venv venv >nul 2>&1
if exist "venv\Scripts\python.exe" (
    set "PY=venv\Scripts\python.exe"
) else (
    set "PY=%SYSTEM_PY%"
)

:CHECK_DEPS
:: 3. Bagimliliklar kurulu mu kontrol et
%PY% -c "import flet, customtkinter, faster_whisper, soundfile, yt_dlp" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    goto :RUN_APP
)

echo Gerekli kutuphaneler kuruluyor (requirements.txt)...
echo Bu islem ilk calistirmada birkac dakika surebilir, lutfen bekleyin...
%PY% -m pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [HATA] Kutuphaneler kurulurken bir sorun olustu.
    pause
    exit /b 1
)

:RUN_APP
echo SesMetin Pro baslatiliyor...
%PY% main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [HATA] Uygulama sonlandi. Kod: %ERRORLEVEL%
    pause
)
