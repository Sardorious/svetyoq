@echo off
REM Ikki marta bosish uchun. PowerShell skriptini ishga tushiradi.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0push.ps1" %*
echo.
pause
