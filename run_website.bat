@echo off
REM Cottonil Manager board (website) - double-click, then open http://localhost:8050
cd /d "%~dp0"
python website\server.py
pause
