# PythonAnywhere Deploy Guide

## 🚀 PythonAnywhere - Eng Yaxshi Bepul Telegram Bot Platformasi

PythonAnywhere bepul plani bor va background workers uchun mos keladi:
- ✅ **Bepul plan** - To'liq bepul
- ✅ **Background workers** - Scheduled tasks bilan ishlaydi
- ✅ **Persistent storage** - Database yo'qolmaydi
- ✅ **Python native** - Docker kerak emas
- ✅ **Easy setup** - Oddiy bash script

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

```bash
git clone https://github.com/obidjon1609/S7UtagBot.git
cd S7UtagBot
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
BOT_TOKEN=8810994701:AAEHEFtJnrYDfXVcUesD-PNqfaMNXsog35I
API_ID=35068149
API_HASH=fb3454704c8dc81b869ebb852069b027
ADMIN_IDS=8347643369
ADMIN_USERNAME=@org_orifovc
ADMIN_USERNAMES=@org_orifovc
DB_FILE=/home/yourusername/pro_tag_bot/database22.db
SOURCE_FILE=/home/yourusername/pro_tag_bot/pro.tag.10.py
```

## 6. Webhookni O'chirish (Muhim!)

Agar oldin bot webhook bilan ishlagan bo'lsa, webhookni o'chirish kerak:

```bash
cd ~/pro_tag_bot
source myenv/bin/activate
python delete_webhook.py
```

Bu Telegram webhookni o'chiradi va polling uchun tayyorlaydi.

## 7. Botni Test Qilish

```bash
cd ~/pro_tag_bot
source myenv/bin/activate
python pro.tag.10.py
```

Bot ishlayotganini tekshiring, keyin `Ctrl+C` bilan to'xtating.

## 8. Always-on Task Sifatida Ishga Tushirish

PythonAnywhere bepul planida background workers yo'q, lekin **scheduled task** orqali ishga tushirish mumkin:

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

## 9. Loglarni Kuzatish

"Tasks" -> "Always-on tasks" -> "Log" orqali bot loglarini ko'rishingiz mumkin.

## 10. Muhim Eslatmalar

### PythonAnywhere Bepul Plan Cheklovlari:
- **To'liq bepul** - Pullik features yo'q
- **512MB RAM** - Yetarli bot uchun
- **Persistent storage** - Database yo'qolmaydi
- **Scheduled tasks** - Background worker sifatida ishlaydi

### Database Persistent:
PythonAnywhere bepul planida `database22.db` fayli doimiy saqlanadi.

### Session Storage:
Telethon sessiyalari bazada saqlanadi, shuning uchun qayta deploy'dan keyin ishlashi kerak.

## 11. Troubleshooting

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

## 12. Yangilash

Yangi versiyani deploy qilganda:
1. Fayllarni yangilang
2. Always-on taskni to'xtating
3. Bir marta test qiling
4. Always-on taskni qayta yoqing

## 🎯 Nima uchun PythonAnywhere?

1. **To'liq bepul** - Pullik features yo'q
2. **Background workers** - Scheduled tasks bilan ishlaydi
3. **Persistent storage** - Database yo'qolmaydi
4. **Python native** - Docker kerak emas
5. **Easy setup** - Oddiy bash script

---

🎉 PythonAnywhere platformasi Telegram botlar uchun eng yaxshi haqiqatan bepul option!