@echo off
REM Folder distribution: dist\Pilgrim Autosplitter\Pilgrim Autosplitter.exe + DLLs.
REM Zip the whole "Pilgrim Autosplitter" folder to share.
cd /d "%~dp0.."
python -m PyInstaller --noconfirm "Pilgrim Autosplitter.spec"
if errorlevel 1 exit /b 1
echo Built: dist\Pilgrim Autosplitter\Pilgrim Autosplitter.exe
