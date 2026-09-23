# Glitch Deploy Guide

## ⚠️ Muhim Ogohlantirish

Glitch asosan **web applications** uchun mo'ljallangan platforma. Telegram botlar uchun uning quyidagi cheklovlari bor:

- **Background processes** - Glitch asosan web apps uchun, background worker processes cheklangan
- **Persistent storage** - Glitch'da persistent storage cheklangan
- **Python support** - Glitch Python uchun to'liq qo'llab-quvvatlamaydi

## 🔄 Tavsiya Etilgan Alternativlar

Telegram botlar uchun quyidagi platformalar yaxshiroq mos keladi:
- **Render** - Docker qo'llab-quvvatlaydi, persistent storage bor
- **Fly.io** - Global deploy, Docker qo'llab-quvvatlaydi
- **Railway** - Bepul plani bor, persistent storage qo'shish mumkin

## 🚀 Agar Glitch'dan Foydalanmoqchi Bo'lsangiz

### 1. Glitch Hisob Yaratish
1. https://glitch.com saytiga o'ting
2. Hisob yarating
3. "New Project" tugmasini bosing

### 2. Project Yaratish
1. "glitch-hello-node" kabi basic project tanlang
2. Project nomini o'zgartiring: `pro-tag-bot`

### 3. Python Sozlash
Glitch'da Python sozlash uchun:

1. `package.json` faylini yarating:
```json
{
  "name": "pro-tag-bot",
  "version": "1.0.0",
  "description": "Telegram bot",
  "main": "server.js",
  "scripts": {
    "start": "node server.js"
  },
  "dependencies": {
    "express": "^4.18.2"
  }
}
```

2. `server.js` faylini yarating (Python process ni boshqarish uchun):
```javascript
const express = require('express');
const { spawn } = require('child_process');
const app = express();

// Python botni boshlash
const pythonProcess = spawn('python3', ['pro.tag.10.py']);

pythonProcess.stdout.on('data', (data) => {
  console.log(`Python stdout: ${data}`);
});

pythonProcess.stderr.on('data', (data) => {
  console.error(`Python stderr: ${data}`);
});

pythonProcess.on('close', (code) => {
  console.log(`Python process exited with code ${code}`);
});

app.get('/', (req, res) => {
  res.send('ProTag Telegram Bot is running');
});

app.listen(3000, () => {
  console.log('Server running on port 3000');
});
```

### 4. Fayllarni Yuklash
1. Glitch dashboardga o'ting
2. Barcha fayllarni Glitchga yuklang:
   - `pro.tag.10.py`
   - `requirements.txt`
   - `.env` (xavfsizlik uchun Glitch'da environment variables sozlang)

### 5. Environment Variables
Glitch'da `.env` fayl orqali environment variables sozlang:

```
BOT_TOKEN=8810994701:AAEHEFtJnrYDfXVcUesD-PNqfaMNXsog35I
API_ID=35068149
API_HASH=fb3454704c8dc81b869ebb852069b027
ADMIN_IDS=8347643369
ADMIN_USERNAME=@org_orifovc
ADMIN_USERNAMES=@org_orifovc
DB_FILE=/tmp/database22.db
SOURCE_FILE=/app/pro.tag.10.py
```

### 6. Python Dependencies
Glitch'da Python dependencies o'rnatish qiyin. Shuning uchun:

1. Terminalni oching
2. Quyidagi buyruqlarni bajaring:
```bash
pip3 install aiogram aiosqlite python-dotenv Telethon
```

## ⚠️ Kutilayotgan Muammolar

1. **Python process** - Glitch'da Python background processes unutil yoki to'xtaydi
2. **Database persistence** - Restartdan keyin database yo'qoladi
3. **Storage limits** - Glitch'da persistent storage cheklangan
4. **Process limits** - Long-running processes uchun mos emas

## 🎯 Tavsiya

Glitch o'rniga **Render** platformasidan foydalaning:
- Telegram botlar uchun mos keladi
- Persistent storage bor
- Docker qo'llab-quvvatlaydi
- Bepul plani bor

## 🔄 Renderga O'tish

Agar Glitch ishlamasa, Render platformasiga o'tish uchun:
1. https://render.com saytiga o'ting
2. GitHub integratsiyasidan foydalaning
3. Dockerfile allaqachon tayyor
4. Environment variables sozlang