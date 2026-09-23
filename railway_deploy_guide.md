# Railway Deploy Guide

## 1. GitHub Repositoriyasini Tayyorlash

Botni Railway ga deploy qilish uchun GitHub repositoriyasi kerak.

### 1.1 GitHub Hisob Yaratish
1. https://github.com saytiga o'ting
2. Hisob yarating (agar bo'lmasa)

### 1.2 Repositoriya Yaratish
1. "New repository" tugmasini bosing
2. Nom: `pro-tag-bot`
3. Public/Private - o'zingiz tanlang
4. "Create repository" tugmasini bosing

### 1.3 Fayllarni Yuklash
Windows PowerShell'da:

```powershell
cd D:\Asosiy\tg-bots\ProTag.10
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/yourusername/pro-tag-bot.git
git push -u origin main
```

**Muhim**: `.env` faylini GitHubga yuklamang! Buning o'rniga `.gitignore` ga qo'shing:

```gitignore
.env
database22.db
.venv/
__pycache__/
*.pyc
```

## 2. Railway Hisob Yaratish

1. https://railway.app saytiga o'ting
2. "Start a new project" tugmasini bosing
3. GitHub bilan ulaning

## 3. Botni Deploy Qilish

### 3.1 GitHub dan Import
1. "Deploy from GitHub repo" ni tanlang
2. `pro-tag-bot` repositoriyasini tanlang
3. "Deploy Now" tugmasini bosing

### 3.2 Sozlamalar
Railway avtomatik Python kodi aniqlaydi va quyidagilarni so'raydi:

1. **Build Command**: `pip install -r requirements.txt`
2. **Start Command**: `python pro.tag.10.py`

## 4. Environment Variables Sozlash

1. Railway dashboardda deploy bo'limiga o'ting
2. "Variables" bo'limiga o'ting
3. Quyidagilarni qo'shing:

```
BOT_TOKEN=your_bot_token
API_ID=your_api_id
API_HASH=your_api_hash
ADMIN_IDS=8347643369
ADMIN_USERNAME=@owapro
ADMIN_USERNAMES=@owapro
DB_FILE=/app/database22.db
SOURCE_FILE=/app/pro.tag.10.py
```

## 5. Persistent Storage Sozlash

Railway bepul planida ephemeral storage ishlaydi, shuning uchun database yo'qolishi mumkin.

### 5.1 Persistent Disk Qo'shish
1. Railway dashboardda "Storage" bo'limiga o'ting
2. "New Volume" tugmasini bosing
3. Nam: `database-volume`
4. Mount path: `/app/data`

### 5.2 Kodni Sozlash
`pro.tag.10.py` faylida DB_FILE yo'lini o'zgartiring:

```python
DB_FILE = os.getenv("DB_FILE", "/app/data/database22.db")
```

## 6. Deploy

1. "Deploy" tugmasini bosing
2. Loglarni kuzating
3. Bot ishga tushganda, `/start` buyrug'ini yuboring

## 7. Loglarni Kuzatish

Railway dashboardda:
- "Deployments" bo'limida deploy loglarini ko'rishingiz mumkin
- "Logs" bo'limida runtime loglarini ko'rishingiz mumkin

## 8. Muhim Eslatmalar

### Railway Bepul Plan Cheklovlari:
- $5 kredit oylab
- Har oyda kreditlar qayta tiklanadi
- 512MB RAM
- Ephemeral storage (qayta deploy'dan keyin ma'lumotlar yo'qolishi mumkin)

### Disk Bilan Ishlash:
```python
# Kodda shunday path ishlating
import os
data_dir = os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "/app/data")
db_path = os.path.join(data_dir, "database22.db")
```

## 9. Troubleshooting

### Bot ishlamayapti:
- Loglarni tekshiring
- Environment variables to'g'ri ekanini tekshiring
- Deploy statusni tekshiring

### Database xatoliklari:
- Persistent volume sozlanganini tekshiring
- Path to'g'ri ekanini tekshiring

### Build xatoliklari:
- `requirements.txt` to'liq ekanini tekshiring
- Python versiyasi mos kelishini tekshiring

## 10. Yangilash

Yangi versiyani deploy qilganda:
1. GitHubga push qiling
2. Railway avtomatik deploy qiladi
3. Loglarni kuzating

## 11. Alternativ: Render

Agar Railway ishlamasa, Render ham yaxshi alternativ:
- https://render.com
- GitHub integratsiyasi
- Persistent storage qo'llab-quvvatlaydi
- Bepul plan bor