# Render Deploy Guide

## 🚀 Render - Telegram Botlar Uchun Eng Yaxshi Bepul Option

Render Telegram botlar uchun mos keladi:
- ✅ Docker qo'llab-quvvatlaydi
- ✅ Persistent storage bor
- ✅ Background processes ishlaydi
- ✅ Bepul plani bor

## 1. Render Hisob Yaratish

1. https://render.com saytiga o'ting
2. "Sign Up" tugmasini bosing
3. GitHub bilan ulaning

## 2. Repositoriyani Import Qilish

1. Dashboardda "New +" tugmasini bosing
2. "Web Service" ni tanlang
3. GitHub repositoriyasini tanlang: `S7UtagBot`
4. "Connect" tugmasini bosing

## 3. Build va Deploy Sozlamalari

Render avtomatik Dockerfile aniqlaydi, lekin quyidagilarni tekshiring:

### Build & Deploy
- **Docker Context**: `/`
- **Dockerfile Path**: `Dockerfile`
- **Runtime**: Docker

## 4. Environment Variables Sozlash

"Environment" bo'limiga quyidagilarni qo'shing:

```
BOT_TOKEN=8810994701:AAEHEFtJnrYDfXVcUesD-PNqfaMNXsog35I
API_ID=35068149
API_HASH=fb3454704c8dc81b869ebb852069b027
ADMIN_IDS=8347643369
ADMIN_USERNAME=@org_orifovc
ADMIN_USERNAMES=@org_orifovc
DB_FILE=/app/database22.db
SOURCE_FILE=/app/pro.tag.10.py
```

## 5. Persistent Disk Sozlash

Render bepul planida persistent disk ishlaydi:

1. Dashboardda Web Service bo'limiga o'ting
2. "Disks" bo'limiga o'ting
3. "Add Disk" tugmasini bosing
4. Quyidagilarni to'ldiring:
   - **Name**: `database-disk`
   - **Mount Path**: `/app/data`
   - **Size**: 1 GB (bepul plan uchun yetarli)

## 6. Kodni Persistent Disk Uchun Sozlash

`pro.tag.10.py` faylida quyidagilarni o'zgartiring:

```python
# Render persistent disk uchun path
data_dir = os.getenv("RENDER_DISK_MOUNT_PATH", os.path.dirname(__file__))
DB_FILE = os.getenv("DB_FILE", os.path.join(data_dir, "database22.db"))
```

## 7. Health Check Sozlash (Ixtiyoriy)

"Health Check" bo'limida:
- **Path**: `/`
- **Check Interval**: 60s
- **Timeout**: 30s
- **Failure Threshold**: 3

## 8. Deploy

1. "Create Web Service" tugmasini bosing
2. Build jarayonini kuzating
3. Bot ishga tushganda, `/start` buyrug'ini yuboring

## 9. Loglarni Kuzatish

Render dashboardda:
- **Logs** bo'limida deploy va runtime loglarini ko'rishingiz mumkin
- **Metrics** bo'limida resurslarni kuzatishingiz mumkin

## 10. Auto-Deploy Sozlash

GitHub'da yangi commit bo'lganda avtomatik deploy uchun:
1. Web Service bo'limiga o'ting
2. "Settings" -> "Auto-Deploy" bo'limiga o'ting
3. "Auto-deploy" ni yoqing

## 💰 Render Bepul Plan Cheklovlari

- 750 hours/month web service time
- 512MB RAM
- Persistent disk (1 GB)
- HTTPS automatically

## 🔧 Troubleshooting

### Bot ishlamayapti:
- Loglarni tekshiring
- Environment variables to'g'ri ekanini tekshiring
- Dockerfile to'g'ri ekanini tekshiring

### Database xatoliklari:
- Persistent disk sozlanganini tekshiring
- `RENDER_DISK_MOUNT_PATH` to'g'ri ekanini tekshiring

### Build xatoliklari:
- Dockerfile syntaxni tekshiring
- `requirements.txt` to'liq ekanini tekshiring

## 🔄 Yangilash

Yangi versiyani deploy qilganda:
1. GitHubga push qiling
2. Render avtomatik deploy qiladi
3. Loglarni kuzating

---

🎉 Render platformasi Telegram botlar uchun eng yaxshi bepul option!