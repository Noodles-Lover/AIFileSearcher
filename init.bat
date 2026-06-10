@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
echo ========================================
echo   AI File Searcher - Project Initialization
echo ========================================
echo.

REM Ask for proxy settings
set USE_PROXY=N
set HTTP_PROXY=
set HTTPS_PROXY=

echo Do you need to use a proxy? (for downloading packages/models)
echo Note: If you encounter SSL errors, try without proxy first
set /p USE_PROXY="Use proxy? (Y/N, default N): "
if /i "!USE_PROXY!"=="Y" (
    set /p HTTP_PROXY="Enter HTTP proxy (e.g. http://127.0.0.1:7890): "
    set /p HTTPS_PROXY="Enter HTTPS proxy (e.g. http://127.0.0.1:7890): "
    
    REM Set environment variables for current session
    set HTTP_PROXY=!HTTP_PROXY!
    set HTTPS_PROXY=!HTTPS_PROXY!
    
    echo Proxy settings applied:
    echo   HTTP_PROXY=!HTTP_PROXY!
    echo   HTTPS_PROXY=!HTTPS_PROXY!
    echo.
    echo Testing proxy connection...
    powershell -Command "try { $r = Invoke-WebRequest -Uri 'https://pypi.org' -Proxy '!HTTP_PROXY!' -TimeoutSec 10 -UseBasicParsing; if ($r.StatusCode -eq 200) { Write-Host 'Proxy test: SUCCESS' } else { Write-Host 'Proxy test: FAILED (Status:' $r.StatusCode ')' } } catch { Write-Host 'Proxy test: FAILED (' $_ ')' }" 
    echo.
)
echo.

REM Check Node.js
echo [1/4] Checking Node.js...
where node >nul 2>&1
if errorlevel 1 (
    echo   Error: Node.js not found. Please install Node.js 16+
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
echo   Node.js version: %NODE_VERSION%

REM Check Python
echo [2/4] Checking Python...
where python >nul 2>&1
if errorlevel 1 (
    echo   Error: Python not found. Please install Python 3.10+
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo   Python version: %PYTHON_VERSION%

REM Install frontend dependencies
echo [3/4] Installing frontend dependencies...
cd frontend
if not "!HTTP_PROXY!"=="" (
    call npm config set proxy !HTTP_PROXY!
    call npm config set https-proxy !HTTPS_PROXY!
)
call npm install
if errorlevel 1 (
    echo   Error: Frontend dependencies installation failed
    cd ..
    pause
    exit /b 1
)
echo   Frontend dependencies installed successfully
cd ..

REM Create Python virtual environment and install backend dependencies
echo [4/4] Setting up backend environment...
cd backend

REM Create virtual environment
if not exist "venv" (
    echo   Creating Python virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo   Error: Virtual environment creation failed
        cd ..
        pause
        exit /b 1
    )
)

REM Install backend dependencies
echo   Installing backend dependencies (this may take a few minutes)...

REM Check if requirements.txt exists, if not try to download from GitHub
if not exist "requirements.txt" (
    echo   Warning: requirements.txt not found, trying to download from GitHub...
    
    REM Try to download using powershell
    powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/Noodles-Lover/AIFileSearcher/main/backend/requirements.txt' -OutFile 'requirements.txt' -UseBasicParsing" >nul 2>&1
    
    if not exist "requirements.txt" (
        echo   Error: Failed to download requirements.txt from GitHub
        echo   Please manually create backend/requirements.txt or re-clone the repository
        echo   GitHub repository: https://github.com/Noodles-Lover/AIFileSearcher
        cd ..
        pause
        exit /b 1
    )
    echo   Downloaded requirements.txt from GitHub
)

if not "!HTTP_PROXY!"=="" (
    echo   Configuring pip to use proxy: !HTTP_PROXY!
    call venv\Scripts\python.exe -m pip config set global.proxy !HTTP_PROXY!
    call venv\Scripts\python.exe -m pip install -r requirements.txt --proxy !HTTP_PROXY! -i https://pypi.tuna.tsinghua.edu.cn/simple --extra-index-url https://download.pytorch.org/whl/cu121 --trusted-host pypi.tuna.tsinghua.edu.cn --trusted-host files.pythonhosted.org --retries 2 --timeout 30
) else (
    call venv\Scripts\python.exe -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --extra-index-url https://download.pytorch.org/whl/cu121 --trusted-host pypi.tuna.tsinghua.edu.cn --trusted-host files.pythonhosted.org --retries 2 --timeout 30
)
if errorlevel 1 (
    echo   Error: Backend dependencies installation failed
    cd ..
    pause
    exit /b 1
)
echo   Backend dependencies installed successfully
cd ..

echo.
echo ========================================
echo   Initialization Complete!
echo ========================================
echo.
echo Next steps:
echo   1. Download models: init_models.bat
echo   2. Start application: start_app.bat
echo.
pause
