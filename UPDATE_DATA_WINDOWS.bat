@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (set PY=py) else (set PY=python)
if not exist .venv %PY% -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r pipeline\requirements.txt
python pipeline\enrich_v7.py
node --check site\assets\app.js
python -m unittest discover -s tests -v
start "" "%CD%\site\index.html"
pause
