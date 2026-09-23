# Railway Quick Start Guide

## 🚀 Tezkor Deploy Qadamlari

Botingiz GitHubga yuklandi! Endi Railway ga deploy qiling.

### 1️⃣ Railway Hisob Yaratish
1. https://railway.app saytiga o'ting
2. "Start a new project" tugmasini bosing
3. GitHub bilan ulaning

### 2️⃣ Repositoriyani Import Qilish
1. "Deploy from GitHub repo" ni tanlang
2. `S7UtagBot` repositoriyasini tanlang
3. "Deploy Now" tugmasini bosing

### 3️⃣ Build Sozlamalari
Railway avtomatik quyidagilarni aniqlaydi:
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python pro.tag.10.py`

Agar so'rasa, quyidagilarni kiriting:
```
Build Command: pip install -r requirements.txt
Start Command: python pro.tag.10.py
```

### 4️⃣ Environment Variables Sozlash
1. Railway dashboardda deploy bo'limiga o'ting
2. "Variables" bo'limiga o'ting
3. Quyidagilarni qo'shing:

```
BOT_TOKEN=your_real_bot_token
API_ID=your_real_api_id
API_HASH=your_real_api_hash
ADMIN_IDS=8347643369
ADMIN_USERNAME=@owapro
ADMIN_USERNAMES=@owapro
DB_FILE=/app/database22.db
SOURCE_FILE=/app/pro.tag.10.py
```

### 5️⃣ Persistent Storage (Muhim!)
Railway bepul planida ephemeral storage ishlaydi. Database yo'qolmasligi uchun:

1. "Storage" bo'limiga o'ting
2. "New Volume" tugmasini bosing
3. Nam: `database-volume`
4. Mount path: `/app/data`
5. Environment variable qo'shing:
```
RAILWAY_VOLUME_MOUNT_PATH=/app/data
```

### 6️⃣ Deploy
1. "Deploy" tugmasini bosing
2. Loglarni kuzating
3. Bot ishga tushganda, `/start` buyrug'ini yuboring

## 📊 Monitoring

- **Deployments**: Deploy loglarini ko'rish
- **Logs**: Runtime loglarini ko'rish
- **Metrics**: Resurslarni kuzatish

## 🔧 Troubleshooting

### Bot ishlamayapti:
- Loglarni tekshiring
- Environment variables to'g'ri ekanini tekshiring
- Build statusni tekshiring

### Database xatoliklari:
- Persistent volume sozlanganini tekshiring
- `RAILWAY_VOLUME_MOUNT_PATH` to'g'ri ekanini tekshiring

## 💰 Bepul Plan Cheklovlari

- $5 kredit oylab
- Har oyda kreditlar qayta tiklanadi
- 512MB RAM
- Ephemeral storage (persistent storage sozlash kerak)

## 🔄 Yangilash

Yangi versiyani deploy qilganda:
1. GitHubga push qiling
2. Railway avtomatik deploy qiladi
3. Loglarni kuzating

---

🎉 Tabriklaymiz! Botingiz Railway bepul serveriga deploy bo'ldi!