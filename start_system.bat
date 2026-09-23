@echo off
title Digital Consumer Complaint Registration & Grievance Redressal System
echo =========================================================================
echo  Digital Consumer Complaint Registration & Grievance Redressal System
echo  Backend: Django 4.2 & Django REST Framework
echo  Database: SQLite (Django ORM)
echo  Frontend: Animated HTML5 / CSS3 / JavaScript Design System
echo =========================================================================
echo.

echo Checking if server is already running...
netstat -ano | findstr :8000 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo [OK] ConsumerCare server is already active on port 8000!
    echo Opening browser at http://127.0.0.1:8000/ ...
    start http://127.0.0.1:8000/
    echo.
    echo Default Logins:
    echo   - Consumer:          rahul_consumer / consumerpass123
    echo   - Authority Officer: officer_admin / adminpass123
    echo.
    pause
    exit /b
)

echo [1/3] Applying database migrations...
python manage.py makemigrations
python manage.py migrate

echo.
echo [2/3] Checking / Seeding demo data...
python seed_data.py

echo.
echo [3/3] Launching web server at http://127.0.0.1:8000/ ...
echo.
echo Default Logins:
echo   - Consumer:          rahul_consumer / consumerpass123
echo   - Authority Officer: officer_admin / adminpass123
echo.
start http://127.0.0.1:8000/
python manage.py runserver 0.0.0.0:8000
pause
