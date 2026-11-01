@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\configure-ai.ps1" -Provider gemini
pause
