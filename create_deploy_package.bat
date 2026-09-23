@echo off
echo PythonAnywhere deploy paketini yaratmoqda...

REM Zip faylni yaratish
powershell -Command "Compress-Archive -Path 'pro.tag.10.py', 'requirements.txt', 'Procfile', 'start.sh', 'pythonanywhere_setup.py', 'pythonanywhere_deploy_guide.md' -DestinationPath 'pro_tag_bot_deploy.zip' -Force"

echo .env faylini qo'shish (xavfsizlik uchun shaxsiy ma'lumotlarni o'zingiz to'ldiring)
powershell -Command "Compress-Archive -Path '.env' -DestinationPath 'pro_tag_bot_deploy.zip' -Update -Force"

echo Deploy paketi tayyor: pro_tag_bot_deploy.zip
echo PythonAnywherega yuklash uchun bu fayldan foydalaning.
pause
