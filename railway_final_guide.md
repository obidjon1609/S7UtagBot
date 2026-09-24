# Railway Final Deploy Guide

## 🚀 Railway - Eng Yaxshi Bepul Telegram Bot Platformasi

Railway bepul plani bor va background workers uchun mos keladi:
- ✅ **Bepul plan** - $5 kredit oylab
- ✅ **Background workers** - To'liq qo'llab-quvvatlaydi
- ✅ **Persistent storage** - Disk qo'shish mumkin
- ✅ **Docker support** - Dockerfile bor
- ✅ **GitHub integratsiyasi** - Avtomatik deploy

## 1. Railway Hisob Yaratish

1. https://railway.app saytiga o'ting
2. "Start a new project" tugmasini bosing
3. GitHub bilan ulaning

## 2. Repositoriyani Import Qilish

1. "Deploy from GitHub repo" ni tanlang
2. `S7UtagBot` repositoriyasini tanlang
3. "Deploy Now" tugmasini bosing

## 3. Build Sozlamalari

Railway avtomatik Dockerfile aniqlaydi:
- **Builder**: Dockerfile
- **Build Command**: Dockerfile'dan o'qiladi
- **Start Command**: `python pro.tag.10.py`

## 4. Environment Variables Sozlash

Railway dashboardda "Variables" bo'limiga quyidagilarni qo'shing:

```
BOT_TOKEN=8810994701:AAEHEFtJnrYDfXVcUesD-PNqfaMNXsog35I
API_ID=35068149
API_HASH=fb3454704c8dc81b869ebb852069b027
ADMIN_IDS=8347643369
ADMIN_USERNAME=@org_orifovc
ADMIN_USERNAMES=@org_orifovc
DB_FILE=/app/data/database22.db
SOURCE_FILE=/app/pro.tag.10.py
RAILWAY_VOLUME_MOUNT_PATH=/app/data
```

## 5. Persistent Volume Sozlash (Muhim!)

Database yo'qolmasligi uchun persistent volume qo'shing:

1. Dashboardda "Storage" bo'limiga o'ting
2. "New Volume" tugmasini bosing
3. Quyidagilarni to'ldiring:
   - **Name**: `database-volume`
   - **Mount Path**: `/app/data`
   - **Size**: 1 GB (bepul plan uchun yetarli)

## 6. Deploy

1. "Deploy" tugmasini bosing
2. Build jarayonini kuzating
3. Bot ishga tushganda, `/start` buyrug'ini yuboring

## 7. Loglarni Kuzatish

Railway dashboardda:
- **Deployments** bo'limida deploy loglarini ko'rishingiz mumkin
- **Logs** bo'limida runtime loglarini ko'rishingiz mumkin
- **Metrics** bo'limida resurslarni kuzatishingiz mumkin

## 8. Auto-Deploy Sozlash

GitHub'da yangi commit bo'lganda avtomatik deploy uchun:
1. Dashboardda service bo'limiga o'ting
2. "Settings" -> "Auto-deploy" bo'limiga o'ting
3. "Auto-deploy" ni yoqing

## 💰 Railway Bepul Plan Cheklovlari

- $5 kredit oylab
- Har oyda kreditlar qayta tiklanadi
- 512MB RAM
- 1 GB persistent storage
- Background workers support

## 🔧 Troubleshooting

### Bot ishlamayapti:
- Loglarni tekshiring
- Environment variables to'g'ri ekanini tekshiring
- Dockerfile to'g'ri ekanini tekshiring

### Database xatoliklari:
- Persistent volume sozlanganini tekshiring
- `RAILWAY_VOLUME_MOUNT_PATH` to'g'ri ekanini tekshiring
- DB_FILE path to'g'ri ekanini tekshiring

### Build xatoliklari:
- Dockerfile syntaxni tekshiring
- `requirements.txt` to'liq ekanini tekshiring
- Logs bo'limida xatolarni ko'ring

## 🔄 Yangilash

Yangi versiyani deploy qilganda:
1. GitHubga push qiling
2. Railway avtomatik deploy qiladi
3. Loglarni kuzating

## 🎯 Nima uchun Railway?

1. **Bepul** - Pullik background worker kerak emas
2. **Background workers** - Telegram botlar uchun mos
3. **Persistent storage** - Database yo'qolmaydi
4. **Docker support** - Dockerfile bilan ishlaydi
5. **GitHub integratsiyasi** - Easy deploy

---

🎉 Railway platformasi Telegram botlar uchun eng yaxshi bepul option!