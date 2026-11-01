@echo off
REM Cottonil Decision Hub (manager website) - double-click, then open http://localhost:8050
cd /d "%~dp0"
python website\server.py
pause
