@echo off
REM Single self-contained Pilgrim Autosplitter.exe (PyInstaller onefile).
REM Run on Windows from repo root: scripts\build-windows.bat
REM Requires: python -m pip install -r requirements.txt pyinstaller

cd /d "%~dp0.."
python -m PyInstaller --noconfirm "Pilgrim Autosplitter-windows-onefile.spec"
if errorlevel 1 exit /b 1
echo Built: dist\Pilgrim Autosplitter.exe
