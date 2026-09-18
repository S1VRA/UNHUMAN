@echo off
setlocal
rem NHModTool release build script.
rem Builds dist\NHModTool.exe (windowed, icon embedded, version resource),
rem then verifies size / icon / selftest and writes dist\SHA256SUMS.txt

cd /d "%~dp0"

echo [1/3] Generating version resource...
python scripts\build_version_info.py
if errorlevel 1 goto :fail

echo [2/3] Building exe with PyInstaller...
python -m PyInstaller --noconfirm --clean NHModTool.spec
if errorlevel 1 goto :fail

echo [3/3] Verifying build...
python scripts\verify_build.py
if errorlevel 1 goto :fail

echo.
echo Build OK: dist\NHModTool.exe
goto :eof

:fail
echo Build FAILED.
exit /b 1