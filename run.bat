@echo off
echo ProTag.10 Botni ishga tushirish...

REM Virtual environment yaratish
if not exist .venv (
    echo Virtual environment yaratilmoqda...
    python -m venv .venv
)

REM Virtual environmentni aktivlashtirish
call .venv\Scripts\activate

REM Dependencies o'rnatish
echo Dependencies o'rnatilmoqda...
pip install --upgrade pip
pip install -r requirements.txt

REM Botni ishga tushirish
echo Botni ishga tushirish...
python pro.tag.10.py

pause
