# ProTag.10

Telegram uchun uTag, userbot boshqaruvi, avtomatik xabar/javob, user yig'ish va admin boshqaruv funksiyalarini birlashtirgan Python bot.

Bot ikki qatlamdan foydalanadi:

- **Aiogram** — bot menyusi, tugmalar, admin panel va Telegram Bot API bilan ishlash.
- **Telethon** — foydalanuvchi o'z Telegram akkauntini ulaganidan keyin `.su`, `.ru`, `.f`, avtomatik javob va profil soati kabi userbot funksiyalarini bajarish.

> **Muhim:** Bu loyiha foydalanuvchining Telegram akkauntiga userbot sessiyasi orqali ulanadi. Faqat o'zingizga tegishli akkauntdan foydalaning, Telegram qoidalariga rioya qiling va sessiya ma'lumotlarini hech kimga bermang.

## Imkoniyatlar

### Oddiy foydalanuvchi funksiyalari

- `/start` orqali botni boshlash va majburiy kanallarga obuna bo'lishni tekshirish.
- Shaxsiy Telegram akkauntini telefon raqami, SMS kodi va kerak bo'lsa 2FA orqali ulash.
- Ulangan akkaunt haqida ism, telefon va uTag holatini ko'rish.
- Akkauntni botdan chiqarish.
- Guruhdagi foydalanuvchilarni bosiladigan mention ko'rinishida tag qilish.
- Guruh a'zolarini ism, username va Telegram ID bilan yig'ish.
- Belgilangan username'larga bir xil xabar yuborish.
- Akkaunt offline bo'lganda shaxsiy xabarlarga avtomatik javob qaytarish.
- Profil familiyasida vaqtni har daqiqada yangilab turuvchi profil soati.
- `.ru` rejimi uchun admin tayyorlagan so'zlar to'plamini tanlash.
- Referal havola orqali PRO olish.
- Admin yoki PRO foydalanuvchilar uchun rozilik bergan qabul qiluvchilarga PM Safe Message yuborish.

### uTag buyruqlari

Buyruqlar ulangan **userbot akkaunti nomidan** guruh ichida yoziladi:

| Buyruq | Vazifasi |
|---|---|
| `.su` yoki `/su` | Guruh ishtirokchilarini ketma-ket tag qiladi |
| `.ru` yoki `/ru` | Tanlangan So'zlar Marketidan tasodifiy so'z bilan tag qiladi |
| `.f` yoki `/f` | Faol uTag jarayonini to'xtatadi |

uTag username mavjud bo'lsa `@username` ko'rinishida, username bo'lmasa Telegram mention entity orqali yuboriladi. Bot o'z akkauntingizni, botlarni va o'chirilgan akkauntlarni o'tkazib yuboradi.

Standart interval 1.5 soniya. Mavjud tanlovlar: 0.5, 1, 1.5, 2, 3 va 5 soniya. Telegram cheklovlariga tushmaslik uchun 1.5-2 soniya tavsiya qilinadi.

### Avto Xabar

`💠 Avto Xabar` bo'limida:

1. Yuboriladigan matnni kiriting.
2. Username'larni har birini yangi qatorda yuboring.
3. Bot ulangan akkaunt orqali xabarlarni yuboradi.

Har bir yuborish orasida taxminan 2 soniya kutadi va yakunda muvaffaqiyatli hamda xatoli yuborishlar sonini ko'rsatadi.

### Avto Javob

`💠 Avto Javob` faqat akkaunt offline bo'lganda shaxsiy xabarlarga javob beradi. Bir xil foydalanuvchiga 15 daqiqa ichida ko'pi bilan bir marta javob yuboriladi.

- Oddiy tarifda javob oxiriga bot reklamasi qo'shiladi.
- PRO tarifda reklama qo'shilmaydi.
- Funksiya javob matnini saqlash orqali yoqiladi, alohida tugma orqali o'chiriladi.

### User Yig'ish

`💠 User Yig'ish` akkaunt ko'ra oladigan guruh yoki megaguruhni tanlash imkonini beradi. Avval guruh a'zolari olinadi, kerak bo'lsa xabarlar tarixidan qo'shimcha userlar topiladi.

- Maksimal so'rov: 500 ta foydalanuvchi.
- Natija bazaga eksport qilinmaydi; bot sizga shu chatning o'zida matn sifatida yuboradi.
- Username'siz foydalanuvchilar ham bosiladigan mention va ID bilan ko'rsatiladi.
- Yopiq guruh uchun ulangan akkaunt guruh a'zosi bo'lishi va ishtirokchilarni ko'ra olishi kerak.

### Profil soat

`Userbotni sozlash` -> `Profil soat` orqali vaqtni akkaunt profilining familiyasiga yozish mumkin.

Qo'llab-quvvatlanadigan vaqt mintaqalari:

- UZ / Asia/Tashkent (UTC+5)
- MSK / Europe/Moscow (UTC+3)
- KZ / Asia/Almaty (UTC+6)
- CET / Europe/Paris (UTC+1)
- EST / America/New_York (UTC-5)
- GMT / Etc/UTC (UTC+0)

Shriftlar: oddiy, qalin, doira, ikki chiziqli, yuqori indeks va monospace. Soat avtomatik ravishda yoqilmaydi; foydalanuvchi alohida `Yoqish` tugmasini bosishi kerak.

### PRO va referal tizimi

PRO quyidagilarni beradi:

- uTag yakunidagi reklamasiz ishlash;
- profil bio'sida reklama bo'lmasligi;
- avto javobda reklama qo'shilmasligi.

Amaldagi tarif: **2 000 UZS / 3 kun**. To'lov bot ichida avtomatik amalga oshirilmaydi; foydalanuvchi admin kontaktiga murojaat qiladi.

Referal havola orqali 3 ta yangi foydalanuvchi taklif qilinganda taklif qiluvchiga 3 kunlik PRO beriladi. PRO tugashidan taxminan 10 daqiqa oldin ogohlantirish yuboriladi.

## Admin panel

Adminlar `/admin` buyrug'i orqali panelni ochadi. Admin ID'lari `ADMIN_IDS` orqali belgilanadi.

Admin panel imkoniyatlari:

- adminlar va loyiha egasi ID'larini ko'rish;
- bot Python fayli yoki ZIP paketini `/source` va `/files` orqali olish;
- majburiy obuna kanallarini qo'shish yoki o'chirish;
- jami foydalanuvchilar va oxirgi 20 foydalanuvchini ko'rish;
- foydalanuvchiga ma'lum kunlik PRO berish;
- So'zlar Marketiga to'plam qo'shish yoki o'chirish;
- barcha foydalanuvchilarga xabar tarqatish;
- konkurs yaratish, faol konkurslarni ko'rish, g'olib tanlash yoki konkursni bekor qilish;
- Safe Management modullarini boshqarish.

### Safe Management

`Safe Management` faqat adminlar uchun mo'ljallangan:

- **Virtual Raqamlar:** raqam, egasi va 30 kunlik amal qilish muddatini hisobga oladi. SMS-verifikatsiya, soxta akkaunt yaratish yoki spamni avtomatlashtirmaydi.
- **Safe Raid/Test:** faqat belgilangan test guruhida, maksimal 10 ta xabar va kamida 3 soniya interval bilan ishlaydi. Flood-limit yoki ko'p xato bo'lsa to'xtaydi.
- **Safe UTag:** faqat bot kuzatgan va opt-in bergan guruh a'zolariga mo'ljallangan xavfsiz rejim. Joriy kodda menyu va sozlamalar mavjud, `Start` tugmasi esa xavfsiz start xabarini qaytaradi.
- **Security Center:** flood, takroriy xabar va havolalarni kuzatadi; xabarni o'chirishi yoki foydalanuvchini 10 daqiqaga cheklashi mumkin. Bot guruhda tegishli admin huquqlariga ega bo'lishi kerak.
- **Haftalik hisobot:** yangi userlar, yig'ilgan yozuvlar va security hodisalari bo'yicha hisobot beradi. Scheduler dushanba kuni 09:00 UTC oynasida yuboradi.
- **Module System:** Safe modullarini alohida yoqish yoki o'chirish holatini saqlaydi.

### PM Safe Message

`PM Safe Message` faqat adminlar va PRO foydalanuvchilar uchun ishlaydi. U faqat bot bilan muloqot qilgan, rozilik bergan va unsubscribe qilmagan foydalanuvchilarga yuboradi.

Kontent turlari:

- matn yoki emoji;
- GIF;
- sticker;
- maksimal 10 ta elementdan iborat aralash kontent.

Xavfsizlik uchun interval 2 soniya. Flood-limit qaytsa kampaniya to'xtaydi, bot bloklangan foydalanuvchini keyingi ro'yxatdan chiqaradi. Har bir xabar ichida foydalanuvchi unsubscribe qilish tugmasi mavjud.

## Texnologiyalar

- Python 3.10+
- Aiogram 3
- Telethon
- SQLite + `aiosqlite`
- `python-dotenv`
- `asyncio`

Asosiy fayl: `pro.tag.10.py`  
Ma'lumotlar bazasi: odatda `database22.db`

## O'rnatish

### Talablar

- Python 3.10 yoki undan yangi versiya;
- Telegram'dan olingan bot token;
- `https://my.telegram.org/apps` saytidan olingan `API_ID` va `API_HASH`;
- Windows uchun PowerShell yoki CMD, server uchun Linux shell.

### Windows'da tezkor ishga tushirish

```powershell
cd C:\Users\obidj\Desktop\ProTag.10
.\run.bat
```

`run.bat` virtual muhit yaratadi, dependency'larni o'rnatadi va botni ishga tushiradi. Birinchi ishga tushirishdan oldin `.env` faylini to'ldiring.

### Qo'lda ishga tushirish

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python pro.tag.10.py
```

PowerShell execution policy muammo bersa, virtual muhitni CMD orqali yoqing:

```bat
.venv\Scripts\activate.bat
```

### Linux serverda ishga tushirish

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python pro.tag.10.py
```

`Procfile` quyidagi worker buyrug'idan foydalanadi:

```text
worker: python pro.tag.10.py
```

`start.sh` esa:

```bash
python pro.tag.10.py
```

## Muhit o'zgaruvchilari

`.env` faylida kamida quyidagilar bo'lishi kerak:

```env
BOT_TOKEN=123456789:telegram_bot_token
API_ID=12345678
API_HASH=telegram_api_hash
```

Ixtiyoriy sozlamalar:

```env
# Qo'shimcha admin ID'lari, vergul bilan ajratiladi
ADMIN_IDS=123456789,987654321

# PRO to'lovi va aloqa tugmasida ko'rsatiladigan admin
ADMIN_USERNAME=@owapro
ADMIN_USERNAMES=@owapro,@other_admin

# SQLite fayli uchun boshqa yo'l
DB_FILE=database22.db

# /source yoki /files yuboradigan Python manba fayli
SOURCE_FILE=pro.tag.10.py
```

`OWNER_ID` kod ichida belgilangan asosiy egadir. `ADMIN_IDS` unga qo'shimcha adminlarni qo'shadi.

> `.env.example` faylidagi `SUB_CHANNEL_ID` va `SUB_CHANNEL_URL` qiymatlari eski konfiguratsiya maydonlaridir. Amaldagi kod majburiy obuna kanallarini SQLite bazasidagi `sub_channels` jadvalidan boshqaradi; kanallarni `/admin` -> `Kanallarni boshqarish` orqali qo'shing.

## Birinchi sozlash

1. BotFather'dan bot yarating va token oling.
2. `my.telegram.org/apps` orqali `API_ID` va `API_HASH` oling.
3. `.env` fayliga qiymatlarni kiriting.
4. Botni ishga tushiring.
5. Admin akkauntidan `/admin` yuborib panelni tekshiring.
6. Majburiy obuna kanallarini qo'shing va botga kerakli kanal huquqlarini bering.
7. Oddiy foydalanuvchi `/start` yuboradi.
8. `Userbotni sozlash` -> `Akkaunt ulash` orqali o'z Telegram akkauntini ulaydi.
9. Telefon raqami, Telegram kodi va kerak bo'lsa 2FA parolini kiriting.
10. Ulangan akkauntni kerakli guruhlarga qo'shib, uTag yoki boshqa userbot funksiyalaridan foydalaning.

Bot har ishga tushganda `database22.db`ni yaratadi va saqlangan Telethon sessiyalarini qayta yuklashga urinadi.

## Ma'lumotlar va xavfsizlik

Quyidagi fayllar maxfiy yoki muhim bo'lishi mumkin:

- `.env` — bot tokeni, API ma'lumotlari va admin sozlamalari;
- `database22.db` — foydalanuvchilar, sozlamalar va Telethon `StringSession` sessiyalari;
- `.venv/` — lokal Python muhit fayllari.

Ularni GitHub, umumiy chat yoki boshqa serverlarga ochiq holda joylamang. Serverda persistent disk ishlating: vaqtinchalik diskda baza yoki sessiya yo'qolsa, barcha akkauntlarni qayta ulash kerak bo'ladi.

Botga kanallarda obunani tekshirish uchun kanalni ko'rish imkoniyati, konkurs xabarlarini yuborish uchun esa kanal yoki guruhda post yuborish huquqi kerak. Security va test modullari uchun botga xabar o'chirish, foydalanuvchini cheklash yoki xabar yuborish kabi admin huquqlarini bering.

## Telegram cheklovlari

Telegram juda ko'p xabar yoki mention yuborishni cheklashi mumkin. Kod `FloodWait` holatlarini kutish yoki kampaniyani to'xtatish orqali boshqaradi, lekin bu cheklovlarni chetlab o'tmaydi.

- uTag tezligini haddan tashqari oshirmang;
- noma'lum yoki roziliksiz foydalanuvchilarga xabar yubormang;
- bir vaqtning o'zida bir nechta agressiv kampaniya boshlamang;
- login kodini qayta-qayta so'ramang;
- flood-limit chiqsa, ko'rsatilgan vaqtni kuting.

## Muammolarni bartaraf etish

### `BOT_TOKEN environment variable is required`

`.env` mavjudligini va `BOT_TOKEN` nomi aynan shunday yozilganini tekshiring. Token qiymatida qo'shimcha bo'sh joy bo'lmasin.

### `API_ID` bilan bog'liq xato

`API_ID` faqat raqam bo'lishi va `API_HASH` bilan bir xil Telegram developer ilovasidan olingan bo'lishi kerak.

### Obuna tekshiruvi ishlamayapti

Botni majburiy kanallarga qo'shing, kerak bo'lsa admin qiling. `/admin` panelidagi kanallar ro'yxatini ham tekshiring.

### Userbot ulanmayapti

Telefon raqamini xalqaro formatda kiriting, masalan `+998901234567`. SMS kodi eskirgan bo'lsa login jarayonini qayta boshlang. 2FA yoqilgan bo'lsa, haqiqiy parolni kiriting.

### uTag userlarni topmayapti

Ulangan akkaunt guruh a'zosi ekanini va ishtirokchilar ro'yxatini ko'ra olishini tekshiring. `.ru` ishlashi uchun avval So'zlar Marketidan to'plam tanlang.

### `FloodWait` yoki `PeerFlood`

Xabar va mention yuborishni to'xtating, Telegram ko'rsatgan kutish vaqtiga rioya qiling va keyin tezlikni pasaytiring.

## Loyiha tuzilishi

```text
ProTag.10/
├── pro.tag.10.py    # Botning barcha handler va worker kodlari
├── requirements.txt  # Python dependency'lari
├── .env              # Maxfiy lokal sozlamalar
├── .env.example      # Eski konfiguratsiya namunasi
├── database22.db    # SQLite baza, ishga tushganda yaratiladi
├── HOSTING.md        # Hosting bo'yicha qisqa ko'rsatma
├── Procfile          # Worker ishga tushirish buyrug'i
├── run.bat           # Windows ishga tushirish skripti
└── start.sh         # Linux ishga tushirish skripti
```

## Litsenziya va foydalanish

Loyiha ichki foydalanish uchun tayyorlangan. Uni ishga tushirishda Telegram API qoidalari, maxfiylik talablari va foydalanuvchilarning roziligiga rioya qilish loyiha egasi zimmasidadir.
