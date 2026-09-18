@echo off
cd /d "%~dp0"
rem Prefer pythonw (no console window). Resolve it next to python.exe when
rem pythonw is not on PATH; fall back to a minimized console otherwise.
for /f "delims=" %%P in ('where python 2^>nul') do (
    if exist "%%~dpPpythonw.exe" (
        start "" "%%~dpPpythonw.exe" "NHModTool.py"
        goto :eof
    )
)
start "" /min python "NHModTool.py"