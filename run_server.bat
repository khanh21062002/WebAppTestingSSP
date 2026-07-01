@echo off
set PYTHONUTF8=1
echo ============================================
echo   SSP Exam System - Local Development
echo ============================================
echo.
echo Starting Django server at http://127.0.0.1:8000
echo.
echo Accounts:
echo   Admin:   admin / Admin@12345
echo   Teacher: giaovien01 / Gv@12345
echo   Student: hocsinh01 / Hs@12345
echo.
echo Press Ctrl+C to stop the server.
echo ============================================
venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
pause
