@echo off
chcp 65001 > nul
title Kurulum - Türkçe Ses Tanıma ^& Konuşmacı Ayrıştırma

cd /d "%~dp0"

echo ==============================================================
echo  Türkçe Ses Tanıma Aracı - Otomatik Kurulum Betiği
echo ==============================================================
echo.

echo 1. Python Sanal Ortamı Kontrol Ediliyor...
if not exist "venv\Scripts\python.exe" (
    echo    Sanal ortam olusturuluyor (venv)...
    python -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo [HATA] Python sanal ortami olusturulamadi!
        pause
        exit /b 1
    )
) else (
    echo    Sanal ortam zaten mevcut.
)

echo.
echo 2. Kütüphaneler Kuruluyor...
.\venv\Scripts\pip.exe install -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo [HATA] Kütüphaneler kurulurken bir sorun oluştu!
    pause
    exit /b 1
)

echo.
echo ==============================================================
echo  Kurulum Başarıyla Tamamlandı!
echo  Uygulamayı başlatmak için run.bat dosyasına çift tıklayabilirsiniz.
echo ==============================================================
echo.
pause
