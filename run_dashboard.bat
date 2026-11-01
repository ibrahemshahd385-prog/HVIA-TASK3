@echo off
REM Cottonil BI and AI dashboard (Streamlit) - double-click to run
cd /d "%~dp0"
if not exist clean\cottonil_clean.pkl (
  echo Building the clean data - about 20 seconds, first time only...
  python core\build_clean.py
)
cd dashboard
python -m streamlit run app.py
pause
