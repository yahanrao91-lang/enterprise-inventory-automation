@echo off
cd /d "%~dp0"
echo ============================================
echo   Inventory Automation System
echo ============================================
echo Starting... Browser will open automatically.
echo Close this window to stop.
echo.
python -m streamlit run app.py
pause
