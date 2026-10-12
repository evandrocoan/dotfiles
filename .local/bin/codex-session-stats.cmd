@echo off
setlocal

where py >NUL
if errorlevel 1 goto python_fallback
py -3 -c "import sqlite3, zoneinfo" >NUL
if not errorlevel 1 goto run_py

:python_fallback
where python >NUL
if errorlevel 1 goto missing_python
python -c "import sqlite3, zoneinfo" >NUL
if not errorlevel 1 goto run_python

:missing_python
echo codex-session-stats: Python 3 with sqlite3 and zoneinfo is required. 1>&2
exit /b 1

:run_py
py -3 "%~dp0codex-session-stats" %*
exit /b %errorlevel%

:run_python
python "%~dp0codex-session-stats" %*
exit /b %errorlevel%
