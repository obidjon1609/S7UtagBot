# PythonAnywhere Deploy Guide

## 1. PythonAnywhere Hisob Yaratish

1. https://www.pythonanywhere.com saytiga o'ting
2. "Create a free account" tugmasini bosing
3. Hisob yarating va tizimga kiring

## 2. Konsolni Sozlash

1. "Consoles" bo'limiga o'ting
2. "Bash" konsol yarating
3. Quyidagi buyruqlarni bajaring:

```bash
cd ~
mkdir pro_tag_bot
cd pro_tag_bot
```

## 3. Fayllarni Yuklash

Fayllarni serverga yuklash uchun ikki usul mavjud:

### Usul 1: Zip fayl orqali

1. Windowsda fayllarni ziplang:
```powershell
Compress-Archive -Path . -DestinationPath pro_tag_bot.zip
```

2. PythonAnywhere konsolida:
```bash
# Zip faylni yuklang (Web interface orqali yoki wget)
unzip pro_tag_bot.zip
rm pro_tag_bot.zip
```

### Usul 2: Git orqali

Agar GitHubda bo'lsa:
```bash
git clone https://github.com/username/repo.git
cd repo
```

## 4. Virtual Environment Yaratish

```bash
python3 -m venv myenv
source myenv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 5. Environment Variables Sozlash

PythonAnywhere dashboarddan:
1. "Account" -> "User Settings" -> "Environment variables"
2. Quyidagilarni qo'shing:

```
BOT_TOKEN=your_bot_token
API_ID=your_api_id
API_HASH=your_api_hash
ADMIN_IDS=8347643369
ADMIN_USERNAME=@owapro
ADMIN_USERNAMES=@owapro
DB_FILE=/home/yourusername/pro_tag_bot/database22.db
SOURCE_FILE=/home/yourusername/pro_tag_bot/pro.tag.10.py
```

## 6. Botni Test Qilish

```bash
cd ~/pro_tag_bot
source myenv/bin/activate
python pro.tag.10.py
```

Bot ishlayotganini tekshiring, keyin `Ctrl+C` bilan to'xtating.

## 7. Always-on Task Sifatida Ishga Tushirish

1. "Tasks" bo'limiga o'ting
2. "Always-on tasks" bo'limiga o'ting
3. "Add an always-on task" tugmasini bosing
4. Quyidagilarni to'ldiring:

- **Description**: ProTag Telegram Bot
- **Source**: Bash script
- **Command**: 
```bash
cd /home/yourusername/pro_tag_bot && source myenv/bin/activate && python pro.tag.10.py
```
- **Minute**: */5 (har 5 daqiqada restart)
- **Save** tugmasini bosing

## 8. Loglarni Kuzatish

"Tasks" -> "Always-on tasks" -> "Log" orqali bot loglarini ko'rishingiz mumkin.

## 9. Muhim Eslatmalar

1. **Database Persistent**: PythonAnywhere bepul planida `database22.db` fayli doimiy saqlanadi
2. **Session Storage**: Telethon sessiyalari bazada saqlanadi, shuning uchun qayta deploy'dan keyin ishlashi kerak
3. **Flood Limits**: Telegram cheklovlariga e'tibor bering
4. **Backup**: `.env` fayli va `database22.db` faylini muntazam backup qiling

## 10. Troubleshooting

### Bot ishlamayapti:
- Loglarni tekshiring
- Environment variables to'g'ri ekanini tekshiring
- Bot token ishlayotganini tekshiring

### Database xatoliklari:
- Fayl yo'li to'g'ri ekanini tekshiring
- Faylga yozish huquqi borligini tekshiring

### Dependencies xatoliklari:
```bash
source myenv/bin/activate
pip install -r requirements.txt --upgrade
```

## 11. Yangilash

Yangi versiyani deploy qilganda:
1. Fayllarni yangilang
2. Always-on taskni to'xtating
3. Bir marta test qiling
4. Always-on taskni qayta yoqing