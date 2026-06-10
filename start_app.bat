@echo off
chcp 65001 >nul
echo ========================================
echo   AI File Searcher - Start Application
echo ========================================
echo.

REM Check backend virtual environment
if not exist "backend\venv" (
    echo Error: Backend virtual environment not found. Please run init.bat first.
    pause
    exit /b 1
)

REM Start frontend dev server (new command prompt window)
echo [1/2] Starting frontend dev server...
start "Frontend Dev Server" cmd /k "cd /d %~dp0frontend && npm run dev"

REM Give frontend some time to start
echo   Waiting 5 seconds for frontend to start...
timeout /t 5 /nobreak >nul

REM Start backend application
echo [2/2] Starting backend application...
cd backend
call venv\Scripts\python.exe gui\main.py
if errorlevel 1 (
    echo Error: Backend startup failed
    cd ..
    pause
    exit /b 1
)

cd ..
echo.
echo Application exited.
pause
