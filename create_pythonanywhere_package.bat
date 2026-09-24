@echo off
echo PythonAnywhere deploy paketini yaratmoqda...

REM Zip faylni yaratish
powershell -Command "Compress-Archive -Path 'pro.tag.10.py', 'requirements.txt', 'delete_webhook.py', 'run.bat', 'hot_reload.bat', 'hot_reload.py', 'pythonanywhere_final_guide.md', '.env.template', 'README.md' -DestinationPath 'pro_tag_bot_pythonanywhere.zip' -Force"

echo .env faylini qo'shish (xavfsizlik uchun shaxsiy ma'lumotlarni o'zingiz to'ldiring)
powershell -Command "Compress-Archive -Path '.env' -DestinationPath 'pro_tag_bot_pythonanywhere.zip' -Update -Force"

echo Deploy paketi tayyor: pro_tag_bot_pythonanywhere.zip
echo PythonAnywherega yuklash uchun bu fayldan foydalaning.
pause
