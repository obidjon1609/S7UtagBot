@echo off
setlocal
if not exist .venv (
    py -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if not exist .env (
    copy .env.example .env
    echo .env yaratildi. Undagi BOT_TOKEN, API_ID va API_HASH qiymatlarini toldiring.
    exit /b 1
)
python pro.tag.10.py
