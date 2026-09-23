@echo off
echo GitHub repositoriyasini tayyorlash...

REM .env faylini backup qilish
if exist .env (
    echo .env faylni backup qilmoqda...
    copy .env .env.backup
    echo .env faylni o'chirib tashlanmoqda (GitIgnore'da bor)...
    del .env
)

REM Git initializatsiya
echo Git initializatsiya...
git init

REM Fayllarni qo'shish
echo Fayllarni qo'shish...
git add .

REM Commit
echo Commit qilmoqda...
git commit -m "Initial commit - ProTag Telegram Bot"

REM Branch nomini o'zgartirish
echo Branch nomini o'zgartirish...
git branch -M main

echo =================================================
echo GitHub repositoriyasi tayyor!
echo =================================================
echo Quyidagi qadamlarni amalga oshiring:
echo 1. GitHubda yangi repositoriya yarating
echo 2. Quyidagi buyruqni bajaring:
echo    git remote add origin https://github.com/yourusername/pro-tag-bot.git
echo 3. Fayllarni yuklang:
echo    git push -u origin main
echo =================================================
echo .
if exist .env.backup (
    echo .env.backup faylini .env ga qaytarish uchun:
    echo    copy .env.backup .env
)
pause
