@echo off
chcp 65001 > nul
title Kurulum ve Calistirma - SesMetin Pro
cd /d "%~dp0"

echo run.bat başlatılıyor...
call "%~dp0run.bat" %*
