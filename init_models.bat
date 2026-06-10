@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
echo ========================================
echo   AI File Searcher - Download Models
echo ========================================
echo.

REM Ask for proxy settings
set USE_PROXY=N
set HTTP_PROXY=
set HTTPS_PROXY=

echo Do you need to use a proxy? (for downloading models from HuggingFace)
set /p USE_PROXY="Use proxy? (Y/N, default N): "
if /i "!USE_PROXY!"=="Y" (
    set /p HTTP_PROXY="Enter HTTP proxy (e.g. http://proxy.example.com:8080): "
    set /p HTTPS_PROXY="Enter HTTPS proxy (e.g. http://proxy.example.com:8080): "
    
    REM Set environment variables for current session
    set HTTP_PROXY=!HTTP_PROXY!
    set HTTPS_PROXY=!HTTPS_PROXY!
    
    echo Proxy settings applied:
    echo   HTTP_PROXY=!HTTP_PROXY!
    echo   HTTPS_PROXY=!HTTPS_PROXY!
)
echo.

REM Check backend virtual environment
if not exist "backend\venv" (
    echo Error: Backend virtual environment not found. Please run init.bat first.
    pause
    exit /b 1
)

REM Check huggingface_hub
echo Checking huggingface_hub...
backend\venv\Scripts\python.exe -c "import huggingface_hub" >nul 2>&1
if errorlevel 1 (
    echo Installing huggingface_hub...
    call backend\venv\Scripts\pip.exe install huggingface-hub
    if errorlevel 1 (
        echo Error: huggingface_hub installation failed
        pause
        exit /b 1
    )
)

REM Start download script
echo Starting model download tool...
cd backend

REM Set proxy environment variables for Python/huggingface_hub
if not "!HTTP_PROXY!"=="" (
    set HTTP_PROXY=!HTTP_PROXY!
    set HTTPS_PROXY=!HTTPS_PROXY!
)

call venv\Scripts\python.exe download_model.py

cd ..
echo.
echo Model download complete!
echo.
echo Next step: Run start_app.bat to start the application
echo.
pause
