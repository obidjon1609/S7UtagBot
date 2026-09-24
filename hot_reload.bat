@echo off
echo ProTag.10 Botni hot reload bilan ishga tushirish...

REM Virtual environmentni aktivlashtirish
call .venv\Scripts\activate

REM Hot reload skriptini ishga tushirish
python hot_reload.py

pause
