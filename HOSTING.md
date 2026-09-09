# ProTag.10 ishga tushirish

## 1. Kerakli ma'lumotlar

- Python 3.10 yoki undan yangi versiya.
- `@BotFather` dan olingan `BOT_TOKEN`.
- `https://my.telegram.org/apps` dan olingan `API_ID` va `API_HASH`.
- Bot uchun Telegram kanallarida admin huquqi: obuna tekshiruvi ishlashi uchun bot kanal a'zolarini ko'ra olishi kerak.
- Userbot ishlatilsa, bot ichidagi `Akkaunt ulash` jarayonida Telegram telefon raqami, SMS kodi va kerak bo'lsa 2FA paroli.

## 2. Lokal Windows ishga tushirish

PowerShell yoki CMD oynasida loyiha papkasiga o'ting:

```powershell
cd C:\Users\obidj\Desktop\ProTag.10
.\run.bat
```

`run.bat` virtual muhit yaratadi, paketlarni o'rnatadi va `.env` bo'lmasa uning shablonini yaratadi. `.env` ni to'ldirgach, `run.bat` ni yana ishga tushiring.

Qo'lda ishga tushirish:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python pro.tag.10.py
```

## 3. `.env` namunasi

```env
BOT_TOKEN=123456789:real_bot_token
API_ID=12345678
API_HASH=real_api_hash
ADMIN_USERNAME=@owapro
```

Haqiqiy token va API ma'lumotlarini hech qachon GitHub yoki umumiy chatga joylamang.

## 4. Birinchi ishga tushirish

1. Botga `/start` yuboring.
2. Admin hisobidan `/admin` buyrug'ini tekshiring.
3. `Userbotni sozlash` -> `Akkaunt ulash` orqali userbot sessiyasini ulang.
4. Bot SQLite bazasini (`database22.db`) o'zi yaratadi.
5. Keyingi ishga tushirishlarda saqlangan sessiyalar bazadan avtomatik yuklanadi.

## 5. Serverga joylash

Python, fayllar va muhit o'zgaruvchilarini serverga yuklang, so'ng:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python pro.tag.10.py
```

Doimiy servis uchun `Procfile` dagi `worker: python pro.tag.10.py` buyruqdan foydalaning. `database22.db` va userbot sessiyalari saqlanadigan disk doimiy bo'lishi kerak; ephemeral disk ishlatilsa, qayta deploydan keyin akkauntni qayta ulashga to'g'ri keladi.

## 6. Muammolar

- `BOT_TOKEN environment variable is required`: `.env` mavjudligini va qiymat nomlari aynan to'g'ri yozilganini tekshiring.
- `API_ID` xatosi: qiymat raqam bo'lishi kerak.
- Obuna tekshiruvi ishlamasa: botni tekshirilayotgan kanallarga admin qilib qo'ying.
- Userbot ulanmasa: `API_ID` va `API_HASH` aynan bir Telegram developer ilovasidan olinganini tekshiring.
- Telegram `FloodWait`: qayta-qayta login yoki xabar yuborishni to'xtatib, ko'rsatilgan vaqtni kuting.
