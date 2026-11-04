@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (echo Python 3.11 is required. Install from https://www.python.org/downloads/windows/ & exit /b 1)
py -3.11 -m pip install --upgrade pip
if errorlevel 1 exit /b 1
py -3.11 -m pip install -r requirements.txt pyinstaller
if errorlevel 1 exit /b 1
py -3.11 -m PyInstaller --noconfirm --clean --onefile --windowed --name AIHub --add-data "assets;assets" main.py
if errorlevel 1 exit /b 1
if not exist "dist\AIHub.exe" (echo Build failed: dist\AIHub.exe not found & exit /b 1)
echo Build complete: "%CD%\dist\AIHub.exe"
endlocal
