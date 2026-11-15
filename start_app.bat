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

REM Start frontend dev server (cmd /c: the window closes automatically when the dev process stops)
echo [1/2] Starting frontend dev server...
start "Frontend Dev Server" cmd /c "cd /d %~dp0frontend && npm run dev"

REM Give frontend some time to start
echo   Waiting 5 seconds for frontend to start...
timeout /t 5 /nobreak >nul

REM Start backend application (blocks until the GUI window is closed)
echo [2/2] Starting backend application...
cd backend
call venv\Scripts\python.exe gui\main.py
if errorlevel 1 (
    echo Error: Backend startup failed
    cd ..
    pause
    exit /b 1
)

REM GUI closed -> stop the frontend dev server (frees port 5173, its window closes with it)
echo Stopping frontend dev server...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173 ^| findstr LISTENING') do taskkill /F /T /PID %%a >nul 2>&1

cd ..
echo Application exited.
