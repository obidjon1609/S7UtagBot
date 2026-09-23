@echo off
setlocal enabledelayedexpansion

set "script=pro.tag.10.py"
set "prev_checksum="

echo Hot reload rejimi faol. %script% kuzatilmoqda...
echo Fayl o'zgarganda bot avtomatik qayta ishga tushadi.
echo To'xtatish uchun Ctrl+C bosing.

call :get_checksum %script% prev_checksum

:loop
call :get_checksum %script% curr_checksum

if not "!curr_checksum!"=="!prev_checksum!" (
    echo %script% o'zgardi. Qayta ishga tushirilmoqda...
    set "prev_checksum=!curr_checksum!"
    
    taskkill /F /IM python.exe >nul 2>&1
    timeout /t 3 >nul
    
    start /B .venv\Scripts\python.exe %script%
)

timeout /t 2 >nul
goto loop

:get_checksum
powershell -Command "(Get-FileHash -Path %1 -Algorithm MD5).Hash.ToLower()" 2>nul
goto :eof