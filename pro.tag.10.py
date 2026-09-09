import asyncio
import html
import logging
import os
import re
import random
import zipfile
import aiosqlite
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, StateFilter, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup,
    Message, CallbackQuery, ReplyKeyboardRemove,
    ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramRetryAfter, TelegramForbiddenError

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError, UserPrivacyRestrictedError, PeerFloodError
from telethon.utils import get_display_name
from telethon.tl.types import UserStatusOnline, MessageEntityMentionName
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.users import GetFullUserRequest

load_dotenv()

logging.basicConfig(level=logging.ERROR)
log = logging.getLogger("@pro_utaggerbot")

def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} environment variable is required")
    return value


API_ID    = int(required_env("API_ID"))
API_HASH  = required_env("API_HASH")
BOT_TOKEN = required_env("BOT_TOKEN")
# Asosiy ega
OWNER_ID = 8332917594
ADMIN_ID = OWNER_ID
ADMIN_IDS = {OWNER_ID}
for admin_id in os.getenv("ADMIN_IDS", "").split(","):
    try:
        if admin_id.strip():
            ADMIN_IDS.add(int(admin_id.strip()))
    except ValueError:
        log.warning("ADMIN_IDS ichida noto'g'ri Telegram ID: %s", admin_id)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "@owapro")
ADMIN_USERNAMES = [
    username.strip() if username.strip().startswith("@") else f"@{username.strip()}"
    for username in os.getenv("ADMIN_USERNAMES", ADMIN_USERNAME).split(",")
    if username.strip()
]
ADMIN_CONTACT_TEXT = " yoki ".join(ADMIN_USERNAMES)
DB_FILE   = os.getenv("DB_FILE", os.path.join(os.path.dirname(__file__), "database22.db"))

AD_TEXT = "🤖 Powered by @pro_utaggerbot 🚀 Bepul Utag xizmati | Bir bosishda tag 🤖."
BIO_AD_TEXT = "🤖 Powered by @pro_utaggerbot 🚀"
AUTO_REPLY_AD = f"{AD_TEXT}\n🤖 @pro_utaggerbot orqali avto javob qilindi."
SOURCE_FILE = os.getenv("SOURCE_FILE", __file__)

storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp  = Dispatcher(storage=storage)

def add_admin_contact_buttons(keyboard: InlineKeyboardBuilder):
    for username in ADMIN_USERNAMES:
        keyboard.row(InlineKeyboardButton(
            text=f"💳 {username} bilan bog'lanish",
            url=f"https://t.me/{username.lstrip('@')}"
        ))

userbot_clients: dict[str, TelegramClient] = {}
_utag_tasks: dict[str, asyncio.Task] = {}
_auto_reply_cooldowns: dict[tuple[str, int], datetime] = {}
_scrape_group_choices: dict[str, dict[str, object]] = {}
_profile_clock_tasks: dict[str, asyncio.Task] = {}
_profile_clock_settings: dict[str, dict[str, str | bool]] = {}
# Bir xil /start buyrug'i tez-tez bosilganda bir xil obuna xabarini
# qayta-qayta yubormaslik uchun kichik deduplikatsiya oynasi.
_start_last_seen: dict[int, datetime] = {}
bot_username = ""

# Profil soati ulanish bilan avtomatik yoqilmaydi. Foydalanuvchi
# "Profil soat" bo'limidan vaqt mintaqasi va shriftni tanlagandan keyin yoqadi.
PROFILE_TIMEZONES = {
    "uz": ("🇺🇿 UZ (UTC+5)", "Asia/Tashkent"),
    "msk": ("🇷🇺 MSK (UTC+3)", "Europe/Moscow"),
    "kz": ("🇰🇿 KZ (UTC+6)", "Asia/Almaty"),
    "cet": ("🇪🇺 CET (UTC+1)", "Europe/Paris"),
    "est": ("🇺🇸 EST (UTC-5)", "America/New_York"),
    "gmt": ("🇬🇧 GMT (UTC+0)", "Etc/UTC"),
}
CLOCK_FONTS = {
    "plain": ("07:04", "Oddiy"),
    "bold": ("𝟎𝟕:𝟎𝟒", "Qalin"),
    "circled": ("⓪⑦:⓪④", "Doira"),
    "double": ("𝟘𝟟:𝟘𝟜", "Ikki chiziqli"),
    "superscript": ("⁰⁷:⁰⁴", "Yuqori indeks"),
    "monospace": ("𝟶𝟽:𝟶𝟺", "Monospace"),
}
CLOCK_DIGIT_STYLES = {
    "plain": "0123456789",
    "bold": "𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗",
    "circled": "⓪①②③④⑤⑥⑦⑧⑨",
    "double": "𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡",
    "superscript": "⁰¹²³⁴⁵⁶⁷⁸⁹",
    "monospace": "𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿",
}

# ─────────────────────────────────────────────
# STATES
# ─────────────────────────────────────────────
class UserStatesGroup(StatesGroup):
    login_phone        = State()
    login_code         = State()
    login_2fa          = State()
    utag_group_link    = State()
    utag_custom_suffix = State()
    utag_speed         = State()
    auto_msg_text      = State()
    auto_msg_usernames = State()
    auto_reply_text    = State()
    scrape_group_select = State()
    scrape_count       = State()
    admin_broadcast        = State()
    admin_add_channel      = State()
    admin_give_pro         = State()
    contest_channel        = State()
    contest_max_users      = State()
    contest_req_channels   = State()
    contest_prize_text     = State()
    admin_market_name      = State()
    admin_market_words     = State()
    pm_content             = State()
    pm_mixed_content       = State()
    vn_number              = State()
    vn_owner               = State()
    safe_test_group        = State()
    safe_test_content      = State()
    safe_utag_word         = State()
    safe_utag_group        = State()
    incident_reason        = State()
    module_toggle          = State()

# ─────────────────────────────────────────────
# DB
# ─────────────────────────────────────────────
async def init_db():
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            fullname TEXT,
            username TEXT,
            referrer_id TEXT,
            pro_until TEXT,
            notified_10m INTEGER DEFAULT 0,
            first_seen TEXT
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            user_id    TEXT,
            account_id TEXT PRIMARY KEY,
            name       TEXT,
            phone      TEXT,
            session    TEXT
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS scraped_users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id   TEXT,
            group_link TEXT,
            telegram_user_id TEXT,
            username   TEXT,
            fullname   TEXT,
            scraped_at TEXT
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS auto_reply_settings (
            owner_id      TEXT PRIMARY KEY,
            enabled       INTEGER DEFAULT 0,
            response_text TEXT NOT NULL,
            updated_at    TEXT
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS utag_settings (
            owner_id TEXT PRIMARY KEY,
            delay    REAL NOT NULL DEFAULT 1.5,
            updated_at TEXT
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS profile_clock_settings (
            owner_id  TEXT PRIMARY KEY,
            enabled   INTEGER NOT NULL DEFAULT 0,
            timezone  TEXT NOT NULL DEFAULT 'Asia/Tashkent',
            font      TEXT NOT NULL DEFAULT 'plain',
            updated_at TEXT
        )""")
        try:
            await db.execute(
                "ALTER TABLE scraped_users ADD COLUMN telegram_user_id TEXT"
            )
        except Exception:
            pass
        await db.commit()
        await db.execute("""
        CREATE TABLE IF NOT EXISTS word_markets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            words TEXT NOT NULL,
            created_at TEXT
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS user_words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id TEXT NOT NULL,
            word TEXT NOT NULL,
            UNIQUE(owner_id, word)
        )""")
        # Kanallar jadval (admin boshqaradi)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS sub_channels (
            channel_username TEXT PRIMARY KEY,
            channel_url      TEXT,
            added_at         TEXT
        )""")
        # Konkurslar
        await db.execute("""
        CREATE TABLE IF NOT EXISTS contests (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id       TEXT,
            message_id    TEXT,
            prize_text    TEXT,
            max_users     INTEGER,
            req_channels  TEXT,
            status        TEXT DEFAULT 'active',
            winner_id     TEXT,
            created_at    TEXT
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS contest_participants (
            contest_id INTEGER,
            user_id    TEXT,
            username   TEXT,
            fullname   TEXT,
            joined_at  TEXT,
            PRIMARY KEY (contest_id, user_id)
        )""")
        # Default kanallar (agar bo'sh bo'lsa)
        async with db.execute("SELECT COUNT(*) FROM sub_channels") as c:
            count = (await c.fetchone())[0]
        if count == 0:
            await db.execute(
                "INSERT OR IGNORE INTO sub_channels VALUES (?,?,?)",
                ("@masteria_group", "https://t.me/masteria_group", datetime.now(timezone.utc).isoformat())
            )
            await db.execute(
                "INSERT OR IGNORE INTO sub_channels VALUES (?,?,?)",
                ("@pro_utager_news", "https://t.me/pro_utager_news", datetime.now(timezone.utc).isoformat())
            )
        await db.commit()


        await db.execute("""
        CREATE TABLE IF NOT EXISTS pm_preferences (
            user_id TEXT PRIMARY KEY,
            consent INTEGER NOT NULL DEFAULT 1,
            unsubscribed INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS pm_drafts (
            owner_id TEXT PRIMARY KEY,
            content_type TEXT NOT NULL,
            content_json TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS pm_campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id TEXT NOT NULL,
            content_type TEXT NOT NULL,
            content_json TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'draft',
            started_at TEXT,
            finished_at TEXT,
            total INTEGER DEFAULT 0,
            success INTEGER DEFAULT 0,
            skipped INTEGER DEFAULT 0,
            failed INTEGER DEFAULT 0,
            stopped INTEGER DEFAULT 0,
            unsubscribed INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS pm_campaign_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER NOT NULL,
            user_id TEXT NOT NULL,
            status TEXT NOT NULL,
            error TEXT,
            created_at TEXT NOT NULL
        )""")
        await db.execute("""
            INSERT OR IGNORE INTO pm_preferences(user_id, consent, unsubscribed, updated_at)
            SELECT id, 1, 0, ? FROM users
        """, (datetime.now(timezone.utc).isoformat(),))
        await db.commit()

        await db.execute("""
        CREATE TABLE IF NOT EXISTS virtual_numbers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            number TEXT NOT NULL,
            owner_id TEXT,
            started_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            warned_3d INTEGER DEFAULT 0,
            warned_1d INTEGER DEFAULT 0,
            created_by TEXT NOT NULL
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS module_settings (
            module TEXT PRIMARY KEY,
            enabled INTEGER NOT NULL DEFAULT 1,
            updated_at TEXT
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS group_security (
            chat_id TEXT PRIMARY KEY,
            title TEXT,
            level TEXT NOT NULL DEFAULT 'medium',
            enabled INTEGER NOT NULL DEFAULT 1,
            flood_threshold INTEGER NOT NULL DEFAULT 5,
            repeat_threshold INTEGER NOT NULL DEFAULT 3,
            updated_at TEXT
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS group_members_activity (
            chat_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            username TEXT,
            fullname TEXT,
            opt_in INTEGER NOT NULL DEFAULT 0,
            last_seen TEXT NOT NULL,
            messages INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY(chat_id, user_id)
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS security_incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL,
            chat_title TEXT,
            user_id TEXT,
            username TEXT,
            reason TEXT NOT NULL,
            action TEXT NOT NULL,
            repeat_count INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            resolved INTEGER DEFAULT 0
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS security_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id TEXT NOT NULL,
            chat_id TEXT,
            user_id TEXT,
            action TEXT NOT NULL,
            details TEXT,
            created_at TEXT NOT NULL
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS safe_test_configs (
            owner_id TEXT PRIMARY KEY,
            chat_id TEXT,
            content TEXT,
            updated_at TEXT
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS safe_campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id TEXT NOT NULL,
            chat_id TEXT NOT NULL,
            content_json TEXT NOT NULL,
            max_messages INTEGER NOT NULL DEFAULT 10,
            interval REAL NOT NULL DEFAULT 3.0,
            status TEXT NOT NULL DEFAULT 'draft',
            started_at TEXT,
            finished_at TEXT,
            sent INTEGER DEFAULT 0,
            failed INTEGER DEFAULT 0,
            stopped INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS weekly_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period_start TEXT NOT NULL,
            period_end TEXT NOT NULL,
            sent_at TEXT NOT NULL
        )""")
        defaults = [
            "virtual_numbers", "safe_test", "safe_utag",
            "security", "weekly_reports", "pm_safe"
        ]
        for mod in defaults:
            await db.execute(
                "INSERT OR IGNORE INTO module_settings(module,enabled,updated_at) VALUES(?,?,?)",
                (mod, 1, datetime.now(timezone.utc).isoformat())
            )
        await db.commit()

# ─────────────────────────────────────────────
# CHANNEL HELPERS
# ─────────────────────────────────────────────

def normalize_channel_username(raw: str) -> str:
    username = (raw or "").strip()
    if not username:
        return ""
    if not username.startswith("@"):
        username = f"@{username}"
    return username


async def get_channels() -> list[dict]:
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT channel_username, channel_url FROM sub_channels") as cur:
            rows = await cur.fetchall()

    channels: list[dict] = []
    for username, url in rows:
        normalized = normalize_channel_username(username)
        if not normalized:
            continue
        channels.append({"username": normalized, "url": url or f"https://t.me/{normalized.lstrip('@')}"})
    return channels


async def check_subscriptions(user_id: int) -> bool:
    channels = await get_channels()
    if not channels:
        return True

    for ch in channels:
        try:
            member = await bot.get_chat_member(chat_id=ch["username"], user_id=user_id)
            if member.status in ["left", "kicked"]:
                return False
        except Exception as exc:
            log.warning("Skipping unreachable or invalid channel %s during subscription check: %s", ch["username"], exc)
            continue
    return True

# ─────────────────────────────────────────────
# PRO HELPERS
# ─────────────────────────────────────────────
def is_pro_user(pro_until_str: str | None) -> bool:
    if not pro_until_str:
        return False
    try:
        until_dt = datetime.fromisoformat(pro_until_str)
        return datetime.now(timezone.utc) < until_dt
    except Exception:
        return False

def make_text_unique(text: str) -> str:
    if not text:
        return ""
    invisible = ["\u200c", "\u200d", "\u200b"]
    return f"{text}{''.join(random.choices(invisible, k=3))}"


# .ru uchun so'zlar endi admin yaratadigan So'zlar Marketidan olinadi.
# Foydalanuvchi tanlagan marketdagi so'zlar bazada saqlanadi.


async def get_utag_delay(uid: str) -> float:
    """uTag oralig'ini bazadan oladi; eski bazalar uchun 1.5 soniya."""
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute(
            "SELECT delay FROM utag_settings WHERE owner_id = ?", (uid,)
        ) as cur:
            row = await cur.fetchone()
    try:
        return max(0.5, min(float(row[0]), 10.0)) if row else 1.5
    except (TypeError, ValueError):
        return 1.5


def make_mention_text(user) -> tuple[str, object | None]:
    """Username bo'lsa @username, bo'lmasa haqiqiy bosiladigan mention."""
    username = getattr(user, "username", None)
    if username:
        return f"@{username}", None

    display = (
        get_display_name(user)
        .replace("#", " ")
        .replace("\n", " ")
        .strip()
        or "Foydalanuvchi"
    )
    length = len(display.encode("utf-16-le")) // 2
    entity = MessageEntityMentionName(
        offset=0,
        length=length,
        user_id=int(user.id),
    )
    return display, entity


async def get_user_words(uid: str) -> list[str]:
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute(
            "SELECT word FROM user_words WHERE owner_id = ? ORDER BY id", (uid,)
        ) as cur:
            return [row[0] for row in await cur.fetchall()]


async def get_market_packs() -> list[tuple[int, str, str]]:
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute(
            "SELECT id, name, words FROM word_markets ORDER BY id DESC"
        ) as cur:
            return await cur.fetchall()


def parse_market_words(text: str) -> list[str]:
    words = []
    for line in text.replace(',', '\n').splitlines():
        word = line.strip()
        if word and word not in words:
            words.append(word)
    return words[:200]


def make_utag_text(user, word: str | None = None) -> tuple[str, object | None]:
    mention, entity = make_mention_text(user)
    text = make_text_unique(mention) if not word else f"{mention}, {word}"
    return text, entity


def build_auto_reply_text(response_text: str, pro: bool) -> str:
    """Foydalanuvchi matnini saqlaydi; reklama faqat oddiy tarifda pastiga tushadi."""
    clean_text = response_text.strip()
    if pro:
        return clean_text
    return f"{clean_text}\n\n{AUTO_REPLY_AD}"

# ─────────────────────────────────────────────
# PROFILE CLOCK — FAMILYA JOYIDA HAR DAQIQA
# ─────────────────────────────────────────────
def format_clock(clock: str, font: str) -> str:
    """HH:MM raqamlarini foydalanuvchi tanlagan shriftga o'tkazadi."""
    digits = CLOCK_DIGIT_STYLES.get(font, CLOCK_DIGIT_STYLES["plain"])
    return "".join(digits[int(char)] if char.isdigit() else char for char in clock)


async def get_profile_clock_settings(uid: str) -> dict[str, str | bool]:
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute(
            "SELECT enabled, timezone, font FROM profile_clock_settings WHERE owner_id = ?",
            (uid,),
        ) as cur:
            row = await cur.fetchone()
    if not row:
        return {"enabled": False, "timezone": "Asia/Tashkent", "font": "plain"}
    return {"enabled": bool(row[0]), "timezone": row[1], "font": row[2]}


async def save_profile_clock_settings(
    uid: str,
    *,
    enabled: bool | None = None,
    tz_name: str | None = None,
    font: str | None = None,
) -> dict[str, str | bool]:
    current = await get_profile_clock_settings(uid)
    next_enabled = bool(current["enabled"]) if enabled is None else enabled
    next_timezone = str(current["timezone"]) if tz_name is None else tz_name
    next_font = str(current["font"]) if font is None else font
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(
            "INSERT OR REPLACE INTO profile_clock_settings "
            "(owner_id, enabled, timezone, font, updated_at) VALUES (?, ?, ?, ?, ?)",
            (
                uid,
                int(next_enabled),
                next_timezone,
                next_font,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        await db.commit()
    return {
        "enabled": next_enabled,
        "timezone": next_timezone,
        "font": next_font,
    }


async def update_profile_clock(client: TelegramClient, settings: dict[str, str | bool]):
    tz_name = str(settings.get("timezone", "Asia/Tashkent"))
    try:
        local_timezone = ZoneInfo(tz_name)
    except Exception:
        local_timezone = timezone(timedelta(hours=5))
    now = datetime.now(local_timezone)
    clock = format_clock(now.strftime("%H:%M"), str(settings.get("font", "plain")))
    await client(UpdateProfileRequest(last_name=clock))


async def profile_clock_watcher(uid: str, client: TelegramClient):
    """Faqat foydalanuvchi yoqqan bo'lsa, familiyani har daqiqa yangilaydi."""
    try:
        while True:
            try:
                settings = await get_profile_clock_settings(uid)
                if not settings["enabled"]:
                    await asyncio.sleep(5)
                    continue
                if not client.is_connected():
                    await client.connect()
                await update_profile_clock(client, settings)
                tz_name = str(settings.get("timezone", "Asia/Tashkent"))
                try:
                    local_timezone = ZoneInfo(tz_name)
                except Exception:
                    local_timezone = timezone(timedelta(hours=5))
                now = datetime.now(local_timezone)
                seconds_to_next_minute = 60 - now.second - (now.microsecond / 1_000_000)
                await asyncio.sleep(max(0.5, seconds_to_next_minute))
            except asyncio.CancelledError:
                raise
            except Exception as e:
                # Bitta vaqtinchalik Telegram/network xatosi soatni
                # butunlay o'chirib qo'ymasligi kerak.
                log.error(f"Profil soati sikli xatosi ({uid}): {e}")
                await asyncio.sleep(10)
    except asyncio.CancelledError:
        raise
    except Exception as e:
        log.error(f"Profil soati xatosi ({uid}): {e}")


def start_profile_clock(uid: str, client: TelegramClient):
    old_task = _profile_clock_tasks.get(uid)
    if old_task and not old_task.done():
        old_task.cancel()
    _profile_clock_tasks[uid] = asyncio.create_task(profile_clock_watcher(uid, client))


def stop_profile_clock(uid: str):
    task = _profile_clock_tasks.pop(uid, None)
    if task and not task.done():
        task.cancel()


def get_profile_clock_keyboard(settings: dict[str, str | bool]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    enabled = bool(settings.get("enabled"))
    tz_name = str(settings.get("timezone", "Asia/Tashkent"))
    font = str(settings.get("font", "plain"))
    tz_label = next(
        (label for label, value in PROFILE_TIMEZONES.values() if value == tz_name),
        tz_name,
    )
    font_label = CLOCK_FONTS.get(font, CLOCK_FONTS["plain"])[1]
    kb.row(
        InlineKeyboardButton(
            text="⏱ O'chirish" if enabled else "⏱ Yoqish",
            callback_data="profile_clock:off" if enabled else "profile_clock:on",
        )
    )
    kb.row(InlineKeyboardButton(text=f"🌍 {tz_label}", callback_data="profile_clock:timezone"))
    kb.row(InlineKeyboardButton(text=f"🔤 Shrift: {font_label}", callback_data="profile_clock:font"))
    kb.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="btn_userbot"))
    return kb.as_markup()


def get_profile_timezone_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for key, (label, _) in PROFILE_TIMEZONES.items():
        kb.row(InlineKeyboardButton(text=label, callback_data=f"profile_clock:tz:{key}"))
    kb.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="profile_clock"))
    return kb.as_markup()


def get_profile_font_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for key, (preview, label) in CLOCK_FONTS.items():
        kb.row(InlineKeyboardButton(text=f"{preview} — {label}", callback_data=f"profile_clock:font:{key}"))
    kb.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="profile_clock"))
    return kb.as_markup()


# ─────────────────────────────────────────────
# PRO BIO MANAGEMENT
# ─────────────────────────────────────────────
async def set_ad_bio(client: TelegramClient, is_pro: bool):
    """Pro bo'lmasa bio ga reklama qoy, pro bo'lsa tozala."""
    if not BIO_AD_TEXT:
        return
    try:
        full = await client(GetFullUserRequest("me"))
        current_bio = full.full_user.about or ""
        if is_pro:
            if BIO_AD_TEXT not in current_bio:
                return
            new_bio = current_bio.replace(BIO_AD_TEXT, "").strip()
        else:
            if BIO_AD_TEXT in current_bio:
                return
            new_bio = (current_bio + "\n" + BIO_AD_TEXT).strip()
        await client(UpdateProfileRequest(about=new_bio[:70]))
    except Exception as e:
        log.error(f"Bio yangilashda xato: {e}")

async def bio_watcher():
    """Har 5 daqiqada barcha ulangan akkauntlar bio'sini tekshiradi va zarur holda yangilaydi."""
    await asyncio.sleep(15)  # Startup ga vaqt ber
    while True:
        try:
            if not AD_TEXT:
                await asyncio.sleep(60)
                continue
            async with aiosqlite.connect(DB_FILE) as db:
                async with db.execute(
                    "SELECT us.user_id, u.pro_until "
                    "FROM user_sessions us "
                    "LEFT JOIN users u ON u.id = us.user_id"
                ) as cur:
                    rows = await cur.fetchall()

            for uid, pro_until in rows:
                if uid not in userbot_clients:
                    continue
                client = userbot_clients[uid]
                try:
                    if not client.is_connected():
                        await client.connect()
                    pro = is_pro_user(pro_until)
                    await set_ad_bio(client, is_pro=pro)
                except Exception as e:
                    log.error(f"bio_watcher akkaunt {uid}: {e}")
        except Exception as e:
            log.error(f"bio_watcher umumiy xato: {e}")
        await asyncio.sleep(300)  # 5 daqiqa

# ─────────────────────────────────────────────
# KEYBOARDS
# ─────────────────────────────────────────────
async def get_sub_keyboard() -> InlineKeyboardMarkup:
    channels = await get_channels()
    kb = InlineKeyboardBuilder()
    for i, ch in enumerate(channels, 1):
        kb.row(InlineKeyboardButton(
            text=f"📢 {i}-kanalga a'zo bo'lish",
            url=ch["url"]
        ))
    kb.row(InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_subscription"))
    return kb.as_markup()

def get_main_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="🔷 Userbotni sozlash", callback_data="btn_userbot"),
        InlineKeyboardButton(text="⚙️ Sozlamalar", callback_data="btn_settings")
    )
    kb.row(
        InlineKeyboardButton(text="💠 Avto Xabar", callback_data="btn_auto_msg"),
        InlineKeyboardButton(text="💠 Avto Javob", callback_data="btn_auto_reply")
    )
    kb.row(
        InlineKeyboardButton(text="💠 User Yig'ish", callback_data="btn_scrape"),
        InlineKeyboardButton(text="⭐ Pro Tarif & Referal", callback_data="btn_pro_info")
    )
    kb.row(InlineKeyboardButton(text="🛒 So'zlar marketi", callback_data="word_market"))
    kb.row(
        InlineKeyboardButton(text="📱 Virtual Raqamlar", callback_data="safe_virtual_numbers"),
        InlineKeyboardButton(text="🛡️ Security Center", callback_data="safe_security")
    )
    kb.row(
        InlineKeyboardButton(text="🧪 Safe Raid/Test", callback_data="safe_test"),
        InlineKeyboardButton(text="📣 Safe UTag", callback_data="safe_utag")
    )
    kb.row(InlineKeyboardButton(text="📊 Haftalik Hisobot", callback_data="safe_weekly"))
    kb.row(InlineKeyboardButton(text="💬 PM Safe Message", callback_data="pm_safe"))
    return kb.as_markup()

def get_userbot_keyboard(acc_name: str | None) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if acc_name:
        kb.row(InlineKeyboardButton(text=f"🟢 Ulangan: {acc_name}", callback_data="noop"))
        kb.row(InlineKeyboardButton(text="ℹ️ Akkaunt ma'lumotlari", callback_data="account_info"))
        kb.row(InlineKeyboardButton(text="⏱ Profil soat", callback_data="profile_clock"))
        kb.row(InlineKeyboardButton(text="🚪 Akkauntdan chiqish", callback_data="logout_account"))
    else:
        kb.row(InlineKeyboardButton(text="📱 Akkaunt ulash", callback_data="add_main_account"))
    kb.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="main_menu"))
    return kb.as_markup()

def back_kb(cb: str = "main_menu") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data=cb))
    return kb.as_markup()

def get_settings_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="📖 uTag qanday ishlaydi?", callback_data="settings_how_utag"))
    kb.row(InlineKeyboardButton(text="⚡ uTag tezligini sozlash", callback_data="settings_utag_speed"))
    kb.row(InlineKeyboardButton(text="💳 Reklama sotib olish (PRO)", callback_data="settings_buy_pro"))
    kb.row(InlineKeyboardButton(text="📢 Kanal havolam", callback_data="settings_my_ref"))
    kb.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="main_menu"))
    return kb.as_markup()


def get_utag_speed_keyboard(delay: float) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    options = (0.5, 1.0, 1.5, 2.0, 3.0, 5.0)
    for value in options:
        label = f"{value:g} soniya"
        if abs(value - delay) < 0.01:
            label = f"✅ {label}"
        kb.row(InlineKeyboardButton(
            text=label,
            callback_data=f"utag_speed:{value:g}"
        ))
    kb.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="btn_settings"))
    return kb.as_markup()

# ─────────────────────────────────────────────
# PRO EXPIRATION CHECKER
# ─────────────────────────────────────────────
async def pro_expiration_checker():
    while True:
        try:
            now = datetime.now(timezone.utc)
            async with aiosqlite.connect(DB_FILE) as db:
                async with db.execute(
                    "SELECT id, pro_until, notified_10m FROM users WHERE pro_until IS NOT NULL"
                ) as cursor:
                    rows = await cursor.fetchall()

                for uid, pro_until_str, notified in rows:
                    if not pro_until_str:
                        continue
                    try:
                        until_dt = datetime.fromisoformat(pro_until_str)
                        time_left = (until_dt - now).total_seconds()
                        if 0 < time_left <= 600 and not notified:
                            try:
                                await bot.send_message(
                                    int(uid),
                                    "⚠️ <b>Sizning pro tarif rejangiz tugamoqda!</b>\n\n"
                                    "Agar yana sotib olmoqchi bo'lsangiz @owapro ga murojaat qiling "
                                    "yoki yana 3 ta do'stingizni botimizga taklif qiling."
                                )
                            except Exception:
                                pass
                            await db.execute(
                                "UPDATE users SET notified_10m = 1 WHERE id = ?", (uid,)
                            )
                            await db.commit()

                        # Pro tugagan — bio dan reklamani olib tashlash (yo'q: qo'shish kerak)
                        if time_left <= 0:
                            # Pro tugadi — agar userbot ulangan bo'lsa, bio ga reklama qo'sh
                            async with db.execute(
                                "SELECT session FROM user_sessions WHERE user_id = ?", (uid,)
                            ) as sc:
                                sess_row = await sc.fetchone()
                            if sess_row and uid in userbot_clients:
                                client = userbot_clients[uid]
                                await set_ad_bio(client, is_pro=False)
                    except Exception:
                        continue
        except Exception as e:
            log.error(f"Checker error: {e}")
        await asyncio.sleep(30)

# ─────────────────────────────────────────────
# START & REFERRAL
# ─────────────────────────────────────────────
@dp.message(CommandStart(), F.chat.type == "private")
async def cmd_start(message: Message, state: FSMContext):
    now = datetime.now(timezone.utc)
    user_id = message.from_user.id
    last_start = _start_last_seen.get(user_id)
    if last_start and (now - last_start).total_seconds() < 3:
        return
    _start_last_seen[user_id] = now

    # Dictionary cheksiz o'sib ketmasligi uchun eski yozuvlarni tozalash.
    if len(_start_last_seen) > 1000:
        cutoff = now - timedelta(minutes=10)
        for seen_user_id, seen_at in list(_start_last_seen.items()):
            if seen_at < cutoff:
                _start_last_seen.pop(seen_user_id, None)

    await state.clear()
    uid = str(user_id)

    if not await check_subscriptions(message.from_user.id):
        await message.answer(
            "⚠️ Botdan foydalanish uchun quyidagi kanallarga a'zo bo'ling:",
            reply_markup=await get_sub_keyboard()
        )
        return

    args = message.text.split()
    referrer_id = args[1] if len(args) > 1 and args[1] != uid else None

    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT id FROM users WHERE id = ?", (uid,)) as cursor:
            user_exists = await cursor.fetchone()

        fullname = message.from_user.full_name or ""
        username = message.from_user.username or ""

        if not user_exists:
            await db.execute(
                "INSERT INTO users (id, fullname, username, referrer_id, pro_until, notified_10m, first_seen) VALUES (?, ?, ?, ?, ?, 0, ?)",
                (uid, fullname, username, referrer_id, None, datetime.now(timezone.utc).isoformat())
            )
            await db.commit()
        else:
            await db.execute(
                "UPDATE users SET fullname = ?, username = ? WHERE id = ?",
                (fullname, username, uid)
            )
            await db.commit()

            if referrer_id:
                async with db.execute(
                    "SELECT COUNT(*) FROM users WHERE referrer_id = ?", (referrer_id,)
                ) as cc:
                    ref_count = (await cc.fetchone())[0]

                if ref_count > 0 and ref_count % 3 == 0:
                    async with db.execute(
                        "SELECT pro_until FROM users WHERE id = ?", (referrer_id,)
                    ) as pc:
                        row = await pc.fetchone()
                        current_pro = row[0] if row else None

                    base_time = datetime.now(timezone.utc)
                    if current_pro and is_pro_user(current_pro):
                        base_time = datetime.fromisoformat(current_pro)

                    new_pro = (base_time + timedelta(days=3)).isoformat()
                    await db.execute(
                        "UPDATE users SET pro_until = ?, notified_10m = 0 WHERE id = ?",
                        (new_pro, referrer_id)
                    )
                    await db.commit()

                    # Pro berildi — bio dan reklamani o'chir
                    if referrer_id in userbot_clients:
                        await set_ad_bio(userbot_clients[referrer_id], is_pro=True)
                    try:
                        await bot.send_message(
                            int(referrer_id),
                            "🎉 <b>Tabriklaymiz!</b> Siz 3 ta do'stingizni taklif qildingiz "
                            "va sizga <b>3 kunlik PRO tarif</b> taqdim etildi!\n\n"
                            "✅ Profil bio'ngizdan reklama olib tashlandi."
                        )
                    except Exception:
                        pass

    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(
            """INSERT INTO pm_preferences (user_id, consent, unsubscribed, updated_at)
               VALUES (?, 1, 0, ?)
               ON CONFLICT(user_id) DO UPDATE SET consent=1, updated_at=excluded.updated_at""",
            (uid, datetime.now(timezone.utc).isoformat())
        )
        await db.commit()

    await message.answer(
        f"💠 Assalom alaykum, <b>{message.from_user.first_name}</b>!\n\n"
        "Ushbu bot orqali o'z Telegram profilingizni ulab, guruhlarda xavfsiz "
        "<b>uTag</b> qilishingiz, <b>avto xabar</b> yuborish va <b>user yig'ish</b> mumkin.",
        reply_markup=get_main_keyboard()
    )

@dp.callback_query(F.data == "check_subscription")
async def cb_check_sub(callback: CallbackQuery, state: FSMContext):
    if await check_subscriptions(callback.from_user.id):
        await callback.answer("✅ Rahmat! Obuna tasdiqlandi.", show_alert=True)
        await callback.message.delete()
        await callback.message.answer(
            f"💠 Assalom alaykum, <b>{callback.from_user.first_name}</b>!\n\n"
            "Ushbu bot orqali o'z Telegram profilingizni ulab, guruhlarda xavfsiz "
            "<b>uTag</b> qilishingiz, <b>avto xabar</b> yuborish va <b>user yig'ish</b> mumkin.",
            reply_markup=get_main_keyboard()
        )
    else:
        await callback.answer("❌ Hali barcha kanallarga a'zo bo'lmadingiz!", show_alert=True)

# ─────────────────────────────────────────────
# MAIN MENU callback
# ─────────────────────────────────────────────
@dp.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery, state: FSMContext):
    if not await check_subscriptions(callback.from_user.id):
        await callback.message.edit_text(
            "⚠️ Avval kanallarga a'zo bo'ling:", reply_markup=await get_sub_keyboard()
        )
        return
    await state.clear()
    await callback.message.edit_text(
        f"💠 Assalom alaykum, <b>{callback.from_user.first_name}</b>!\n\n"
        "Ushbu bot orqali o'z Telegram profilingizni ulab, guruhlarda xavfsiz "
        "<b>uTag</b> qilishingiz, <b>avto xabar</b> yuborish va <b>user yig'ish</b> mumkin.",
        reply_markup=get_main_keyboard()
    )

@dp.callback_query(F.data == "noop")
async def cb_noop(callback: CallbackQuery):
    await callback.answer()

# ─────────────────────────────────────────────
# SOZLAMALAR (SETTINGS)
# ─────────────────────────────────────────────
@dp.callback_query(F.data == "btn_settings")
async def cb_settings(callback: CallbackQuery):
    await callback.message.edit_text(
        "⚙️ <b>Sozlamalar</b>\n\nQuyidagi bo'limlardan birini tanlang:",
        reply_markup=get_settings_keyboard()
    )

@dp.callback_query(F.data == "settings_how_utag")
async def cb_how_utag(callback: CallbackQuery):
    text = (
        "📖 <b>uTag qanday ishlaydi?</b>\n\n"
        "1️⃣ Botga akkauntingizni ulang (<b>Userbotni sozlash</b>)\n"
        "2️⃣ Bot qo'shilgan guruhga kiring\n"
        "3️⃣ Guruhda <code>.su</code> yoki <code>/su</code> yozing → uTag boshlanadi\n"
        "4️⃣ Kulgili random uTag uchun <code>.ru</code> yoki <code>/ru</code> yozing\n"
        "5️⃣ Guruhda <code>.f</code> yoki <code>/f</code> yozing → uTag to'xtatiladi\n\n"
        "⚡ uTag tezligini Sozlamalar → <b>uTag tezligini sozlash</b> bo'limidan "
        "o'zgartirishingiz mumkin.\n"
        "🎲 Random rejimda username yoniga tasodifiy kulgili so'z va sticker "
        "qo'shiladi. Hashtag ishlatilmaydi.\n\n"
        "🔹 <b>Pro tarif bo'lmasa:</b> Tag tugaganda yoki to'xtatilganda reklama matni chiqadi\n"
        "🔹 <b>Pro tarif bo'lsa:</b> Reklama chiqmaydi, bio ham toza qoladi\n\n"
        "💡 <b>Reklama matn:</b>\n"
        f"<code>{AD_TEXT}</code>"
    )
    await callback.message.edit_text(text, reply_markup=back_kb("btn_settings"))


@dp.callback_query(F.data == "settings_utag_speed")
async def cb_utag_speed(callback: CallbackQuery):
    uid = str(callback.from_user.id)
    delay = await get_utag_delay(uid)
    await callback.message.edit_text(
        "⚡ <b>uTag tezligi</b>\n\n"
        f"Hozirgi tezlik: <b>har {delay:g} soniyada 1 ta tag</b>\n\n"
        "Tezlikni tanlang. Juda tez yuborish Telegram chekloviga olib kelishi "
        "mumkin, shuning uchun xavfsiz variant sifatida 1.5–2 soniya tavsiya qilinadi.",
        reply_markup=get_utag_speed_keyboard(delay)
    )


@dp.callback_query(F.data.startswith("utag_speed:"))
async def cb_set_utag_speed(callback: CallbackQuery):
    uid = str(callback.from_user.id)
    try:
        delay = float(callback.data.split(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("❌ Tezlik noto'g'ri.", show_alert=True)
        return

    if delay not in {0.5, 1.0, 1.5, 2.0, 3.0, 5.0}:
        await callback.answer("❌ Bu tezlik mavjud emas.", show_alert=True)
        return

    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(
            "INSERT OR REPLACE INTO utag_settings (owner_id, delay, updated_at) "
            "VALUES (?, ?, ?)",
            (uid, delay, datetime.now(timezone.utc).isoformat())
        )
        await db.commit()

    await callback.answer(f"✅ uTag tezligi har {delay:g} soniyaga o'rnatildi.")
    await callback.message.edit_text(
        "⚡ <b>uTag tezligi</b>\n\n"
        f"Hozirgi tezlik: <b>har {delay:g} soniyada 1 ta tag</b>\n\n"
        "Tezlikni o'zgartirish uchun quyidagi tugmalardan foydalaning.",
        reply_markup=get_utag_speed_keyboard(delay)
    )


@dp.callback_query(F.data == "settings_buy_pro")
async def cb_buy_pro(callback: CallbackQuery):
    text = (
        "💳 <b>PRO Tarif Sotib Olish</b>\n\n"
        "✅ Reklamasiz uTag\n"
        "✅ Bio da reklama yo'q\n"
        "✅ Barcha funksiyalar cheksiz\n\n"
        "💰 Narx: <b>2,000 UZS</b> (3 kunlik)\n\n"
        f"To'lov uchun: {ADMIN_CONTACT_TEXT} ga murojaat qiling"
    )
    kb = InlineKeyboardBuilder()
    add_admin_contact_buttons(kb)
    kb.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="btn_settings"))
    await callback.message.edit_text(text, reply_markup=kb.as_markup())

@dp.callback_query(F.data == "settings_my_ref")
async def cb_my_ref(callback: CallbackQuery):
    uid = str(callback.from_user.id)
    await callback.message.edit_text(
        f"📢 <b>Sizning referal havolangiz:</b>\n\n"
        f"<code>https://t.me/{bot_username}?start={uid}</code>\n\n"
        "3 ta do'stingizni taklif qiling — <b>3 kunlik PRO tarif</b> oling!",
        reply_markup=back_kb("btn_settings")
    )

# ─────────────────────────────────────────────
# PRO PANEL
# ─────────────────────────────────────────────
@dp.callback_query(F.data == "btn_pro_info")
async def cb_pro_info(callback: CallbackQuery):
    uid = str(callback.from_user.id)
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT pro_until FROM users WHERE id = ?", (uid,)) as cursor:
            row = await cursor.fetchone()
            pro_until = row[0] if row else None
        async with db.execute("SELECT COUNT(*) FROM users WHERE referrer_id = ?", (uid,)) as cr:
            ref_count = (await cr.fetchone())[0]

    status = "🔴 Odatiy (Reklamali)"
    if is_pro_user(pro_until):
        until_dt = datetime.fromisoformat(pro_until).strftime("%Y-%m-%d %H:%M")
        status = f"🟢 PRO ({until_dt} gacha reklamasiz)"

    text = (
        f"💠 <b>PRO Tarif Ma'lumotlari</b>\n\n"
        f"Holatingiz: <b>{status}</b>\n"
        f"Chaqirgan do'stlar: <b>{ref_count} ta</b>\n\n"
        f"📌 <b>PRO imkoniyati:</b> Tag ostidagi reklama matni olib tashlanadi!\n\n"
        f"💡 <b>PRO olish:</b>\n"
        f"1️⃣ <b>3 ta do'st taklif qiling</b> → Avto 3 kunlik PRO\n"
        f"2️⃣ <b>Karta orqali:</b> 2,000 UZS (3 kunlik)\n\n"
        f"🔗 Referal havolangiz:\n<code>https://t.me/{bot_username}?start={uid}</code>"
    )
    kb = InlineKeyboardBuilder()
    add_admin_contact_buttons(kb)
    kb.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="main_menu"))
    await callback.message.edit_text(text, reply_markup=kb.as_markup())

# ─────────────────────────────────────────────
# USERBOT MENU
# ─────────────────────────────────────────────
@dp.callback_query(F.data == "btn_userbot")
async def cb_userbot_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    uid = str(callback.from_user.id)
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT account_id, name FROM user_sessions WHERE user_id = ?", (uid,)) as cursor:
            row = await cursor.fetchone()
    acc_name = row[1] if row else None
    await callback.message.edit_text(
        "🔷 <b>Userbot Boshqaruv Markazi</b>\n\nQuyidagi amallardan birini tanlang:",
        reply_markup=get_userbot_keyboard(acc_name)
    )


@dp.callback_query(F.data == "profile_clock")
async def cb_profile_clock(callback: CallbackQuery):
    uid = str(callback.from_user.id)
    if uid not in userbot_clients:
        await callback.answer("❗ Avval akkaunt ulang!", show_alert=True)
        return
    await callback.message.edit_text(
        "⏱ <b>Profil soat</b>\n\n"
        "Avval vaqt mintaqasini tanlang:",
        reply_markup=get_profile_timezone_keyboard(),
    )


@dp.callback_query(F.data.startswith("profile_clock:tz:"))
async def cb_profile_clock_timezone(callback: CallbackQuery):
    uid = str(callback.from_user.id)
    if uid not in userbot_clients:
        await callback.answer("❗ Avval akkaunt ulang!", show_alert=True)
        return
    key = callback.data.rsplit(":", 1)[-1]
    timezone_option = PROFILE_TIMEZONES.get(key)
    if not timezone_option:
        await callback.answer("❌ Vaqt mintaqasi topilmadi.", show_alert=True)
        return
    label, tz_name = timezone_option
    await save_profile_clock_settings(uid, tz_name=tz_name)
    await callback.message.edit_text(
        f"✅ Vaqt mintaqasi tanlandi: <b>{label}</b>\n\n"
        "Endi profil soatining shriftini tanlang:",
        reply_markup=get_profile_font_keyboard(),
    )


@dp.callback_query(F.data == "profile_clock:timezone")
async def cb_profile_clock_change_timezone(callback: CallbackQuery):
    await callback.message.edit_text(
        "🌍 <b>Vaqt mintaqasini tanlang:</b>",
        reply_markup=get_profile_timezone_keyboard(),
    )


@dp.callback_query(F.data == "profile_clock:font")
async def cb_profile_clock_change_font(callback: CallbackQuery):
    await callback.message.edit_text(
        "🔤 <b>Profil soati shriftini tanlang:</b>",
        reply_markup=get_profile_font_keyboard(),
    )


@dp.callback_query(F.data.startswith("profile_clock:font:"))
async def cb_profile_clock_font(callback: CallbackQuery):
    uid = str(callback.from_user.id)
    font = callback.data.rsplit(":", 1)[-1]
    if font not in CLOCK_FONTS:
        await callback.answer("❌ Shrift topilmadi.", show_alert=True)
        return
    settings = await save_profile_clock_settings(uid, font=font)
    await callback.answer("✅ Shrift saqlandi.")
    await callback.message.edit_text(
        "⏱ <b>Profil soat sozlamalari</b>\n\n"
        f"Holati: <b>{'🟢 Yoqilgan' if settings['enabled'] else '🔴 O‘chirilgan'}</b>\n"
        "Profil familiyasiga vaqt har daqiqada yoziladi.\n\n"
        "Soat faqat «Yoqish» tugmasini bosganingizdan keyin ishlaydi.",
        reply_markup=get_profile_clock_keyboard(settings),
    )


@dp.callback_query(F.data == "profile_clock:on")
async def cb_profile_clock_on(callback: CallbackQuery):
    uid = str(callback.from_user.id)
    client = userbot_clients.get(uid)
    if not client:
        await callback.answer("❗ Avval akkaunt ulang!", show_alert=True)
        return
    settings = await save_profile_clock_settings(uid, enabled=True)
    start_profile_clock(uid, client)
    await callback.answer("✅ Profil soat yoqildi.")
    await callback.message.edit_text(
        "⏱ <b>Profil soat sozlamalari</b>\n\n"
        "Holati: <b>🟢 Yoqilgan</b>\n"
        "Vaqt familiya joyiga har daqiqada yangilanadi.",
        reply_markup=get_profile_clock_keyboard(settings),
    )


@dp.callback_query(F.data == "profile_clock:off")
async def cb_profile_clock_off(callback: CallbackQuery):
    uid = str(callback.from_user.id)
    settings = await save_profile_clock_settings(uid, enabled=False)
    stop_profile_clock(uid)
    await callback.answer("⛔ Profil soat o‘chirildi.")
    await callback.message.edit_text(
        "⏱ <b>Profil soat sozlamalari</b>\n\n"
        "Holati: <b>🔴 O‘chirilgan</b>\n"
        "Soat endi profil familiyasiga avtomatik yozilmaydi.",
        reply_markup=get_profile_clock_keyboard(settings),
    )

@dp.callback_query(F.data == "account_info")
async def cb_account_info(callback: CallbackQuery):
    uid = str(callback.from_user.id)
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute(
            "SELECT name, phone FROM user_sessions WHERE user_id = ?", (uid,)
        ) as cur:
            row = await cur.fetchone()
    if not row:
        await callback.answer("Akkaunt topilmadi!", show_alert=True)
        return
    name, phone = row
    utag_active = uid in _utag_tasks and not _utag_tasks[uid].done()
    await callback.message.edit_text(
        f"ℹ️ <b>Akkaunt ma'lumotlari</b>\n\n"
        f"👤 Ism: <b>{name}</b>\n"
        f"📱 Telefon: <b>{phone}</b>\n"
        f"🔄 uTag holati: <b>{'Faol ✅' if utag_active else 'Faol emas ❌'}</b>",
        reply_markup=back_kb("btn_userbot")
    )

# ─────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────
@dp.callback_query(F.data == "add_main_account")
async def cb_add_main_account(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Telefon raqamni ulash", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await bot.send_message(
        callback.from_user.id,
        "Telefon raqamingizni yuborish uchun pastdagi tugmani bosing\n"
        "yoki raqamni yozing (masalan: +998901234567):",
        reply_markup=kb
    )
    await state.set_state(UserStatesGroup.login_phone)

@dp.message(StateFilter(UserStatesGroup.login_phone), F.contact)
async def contact_input(message: Message, state: FSMContext):
    await process_phone_login(message, state, message.contact.phone_number)

@dp.message(StateFilter(UserStatesGroup.login_phone), F.text)
async def text_phone_input(message: Message, state: FSMContext):
    phone = re.sub(r"[.\s\-]", "", message.text.strip())
    if not phone.startswith("+"):
        phone = "+" + phone
    await process_phone_login(message, state, phone)

async def process_phone_login(message: Message, state: FSMContext, phone: str):
    await message.answer("⏳ Telegram serveriga ulanish...", reply_markup=ReplyKeyboardRemove())
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    try:
        await client.connect()
        sent = await client.send_code_request(phone)
        await state.update_data(temp_client=client, phone=phone, phone_code_hash=sent.phone_code_hash)
        await message.answer("📩 Tasdiqlash kodi yuborildi. Kodni kiriting (masalan: 12345):")
        await state.set_state(UserStatesGroup.login_code)
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}")

@dp.message(StateFilter(UserStatesGroup.login_code), F.text)
async def code_input(message: Message, state: FSMContext):
    code = re.sub(r"[.\s\-]", "", message.text.strip())
    data   = await state.get_data()
    client: TelegramClient = data.get("temp_client")
    phone  = data.get("phone")
    hash_v = data.get("phone_code_hash")
    if not client:
        await message.answer("⚠️ Sessiya eskirgan. Qaytadan urinib ko'ring.")
        await state.clear()
        return
    try:
        await client.sign_in(phone, code, phone_code_hash=hash_v)
        await finalize_login(message.from_user.id, client, phone, state)
    except Exception as e:
        err_str = str(e)
        if "Password" in err_str or "SessionPasswordNeeded" in err_str or "Two-steps" in err_str:
            await state.update_data(temp_client=client)
            await state.set_state(UserStatesGroup.login_2fa)
            await message.answer("🔒 2FA parolini kiriting:")
        else:
            await message.answer(f"❌ Kod xato yoki eskirgan: {e}")

@dp.message(StateFilter(UserStatesGroup.login_2fa), F.text)
async def two_fa_input(message: Message, state: FSMContext):
    data   = await state.get_data()
    client: TelegramClient = data.get("temp_client")
    phone  = data.get("phone")
    if not client:
        await message.answer("⚠️ Sessiya eskirgan.")
        await state.clear()
        return
    try:
        await client.sign_in(password=message.text.strip())
        await finalize_login(message.from_user.id, client, phone, state)
    except Exception as e:
        await message.answer(f"❌ Parol noto'g'ri: {e}\nQaytadan kiriting:")

async def finalize_login(user_id: int, client: TelegramClient, phone: str, state: FSMContext):
    me          = await client.get_me()
    acc_id      = str(me.id)
    name        = get_display_name(me)
    session_str = client.session.save()
    uid         = str(user_id)

    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            INSERT OR REPLACE INTO user_sessions (user_id, account_id, name, phone, session)
            VALUES (?, ?, ?, ?, ?)
        """, (uid, acc_id, name, phone, session_str))
        await db.commit()

    userbot_clients[uid] = client
    await register_userbot_handlers(client, uid)
    clock_settings = await get_profile_clock_settings(uid)
    if clock_settings["enabled"]:
        start_profile_clock(uid, client)

    # Pro holatini tekshirib bio yangilaymiz
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT pro_until FROM users WHERE id = ?", (uid,)) as cur:
            row = await cur.fetchone()
    pro_until = row[0] if row else None
    pro = is_pro_user(pro_until)
    await set_ad_bio(client, is_pro=pro)

    await state.clear()
    await bot.send_message(
        user_id,
        f"✅ <b>{name}</b> akkaunti muvaffaqiyatli ulandi!\n\n"
        f"{'🟢 PRO tarif faol — reklama yo‘q' if pro else '🔴 Oddiy tarif — reklama bio ga qo‘yildi'}",
        reply_markup=get_main_keyboard()
    )

# ─────────────────────────────────────────────
# LOGOUT
# ─────────────────────────────────────────────
@dp.callback_query(F.data == "logout_account")
async def cb_logout(callback: CallbackQuery, state: FSMContext):
    uid = str(callback.from_user.id)
    # Profil soatini to'xtat
    stop_profile_clock(uid)
    # uTag ni to'xtat
    if uid in _utag_tasks and not _utag_tasks[uid].done():
        _utag_tasks[uid].cancel()

    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("DELETE FROM user_sessions WHERE user_id = ?", (uid,))
        await db.commit()

    if uid in userbot_clients:
        try:
            await userbot_clients[uid].disconnect()
        except Exception:
            pass
        del userbot_clients[uid]

    await state.clear()
    await callback.message.edit_text(
        "🚪 Akkaunt chiqarildi.",
        reply_markup=get_userbot_keyboard(None)
    )

# ─────────────────────────────────────────────
# UTAG — GURUHDA .su/.f yoki /su /f orqali
# ─────────────────────────────────────────────
async def do_utag(client: TelegramClient, uid: str, event, random_mode: bool = False):
    """.su oddiy tag qiladi, .ru esa foydalanuvchi tanlagan market so'zlaridan foydalanadi."""
    chat = await event.get_chat()
    pro_until = None
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT pro_until FROM users WHERE id = ?", (uid,)) as cur:
            row = await cur.fetchone()
        pro_until = row[0] if row else None
    pro = is_pro_user(pro_until)

    try:
        # Guruh a'zolarini bevosita olamiz. iter_messages() faqat xabar
        # yozganlarni topadi, shuning uchun u orqali ayrim profillar
        # o'tkazib yuborilardi.
        participants = []
        async for participant in client.iter_participants(chat, limit=None):
            participants.append(participant)
        me = await client.get_me()
        delay = await get_utag_delay(uid)
        tagged = 0
        market_words = await get_user_words(uid) if random_mode else []
        if random_mode and not market_words:
            try:
                await client.send_message(chat, "❌ .ru uchun hali So'zlar Marketidan so'z tanlanmagan. Botdagi 🛒 So'zlar marketi bo'limidan tanlang.")
            except Exception:
                pass
            return

        for user in participants:
            if uid not in _utag_tasks or _utag_tasks[uid].done():
                break  # To'xtatildi
            if user.id == me.id or user.bot or getattr(user, "deleted", False):
                continue
            try:
                # Username bor bo'lsa @username, username yo'q bo'lsa
                # Telegramning haqiqiy MentionName entitysi ishlatiladi.
                # Shu sababli profil yashirin bo'lsa ham bosilganda o'sha user ochiladi.
                word = random.choice(market_words) if random_mode else None
                tag_text, tag_entity = make_utag_text(user, word=word)
                if tag_entity:
                    await client.send_message(
                        chat,
                        tag_text,
                        formatting_entities=[tag_entity],
                    )
                else:
                    await client.send_message(chat, tag_text)
                tagged += 1
                await asyncio.sleep(delay)
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds + 5)
            except (UserPrivacyRestrictedError, PeerFloodError):
                continue
            except Exception as e:
                log.error(f"Tag xatosi: {e}")
                continue

        # Jarayon tugadi yoki to'xtatildi — reklama (pro bo'lmasa)
        if not pro:
            try:
                await client.send_message(chat, AD_TEXT)
            except Exception:
                pass

    except asyncio.CancelledError:
        # To'xtatildi — reklama (pro bo'lmasa)
        if not pro:
            try:
                await client.send_message(chat, AD_TEXT)
            except Exception:
                pass
    except Exception as e:
        log.error(f"uTag xatosi: {e}")

async def register_userbot_handlers(client: TelegramClient, uid: str):
    """Userbot uchun guruh event handlerlarini ro'yxatdan o'tkazish."""

    async def is_auto_reply_enabled() -> tuple[bool, str | None]:
        async with aiosqlite.connect(DB_FILE) as db:
            async with db.execute(
                "SELECT enabled, response_text FROM auto_reply_settings WHERE owner_id = ?",
                (uid,)
            ) as cur:
                row = await cur.fetchone()
        return bool(row and row[0]), row[1] if row else None

    @client.on(events.NewMessage(incoming=True))
    async def on_incoming_message(event):
        """Offline paytda kelgan shaxsiy xabarga sozlangan javobni yuboradi."""
        if not event.is_private or not event.raw_text:
            return
        sender = await event.get_sender()
        if not sender or getattr(sender, "bot", False) or getattr(sender, "id", None) is None:
            return

        enabled, response_text = await is_auto_reply_enabled()
        if not enabled or not response_text:
            return

        try:
            me = await client.get_me()
            if isinstance(getattr(me, "status", None), UserStatusOnline):
                return
            cooldown_key = (uid, int(sender.id))
            last_sent = _auto_reply_cooldowns.get(cooldown_key)
            now = datetime.now(timezone.utc)
            if last_sent and (now - last_sent).total_seconds() < 900:
                return

            async with aiosqlite.connect(DB_FILE) as db:
                async with db.execute(
                    "SELECT pro_until FROM users WHERE id = ?", (uid,)
                ) as cur:
                    row = await cur.fetchone()
            pro = is_pro_user(row[0] if row else None)
            reply_text = build_auto_reply_text(response_text, pro)
            await event.respond(reply_text)
            _auto_reply_cooldowns[cooldown_key] = now
        except FloodWaitError as exc:
            await asyncio.sleep(exc.seconds)
        except Exception as exc:
            log.error(f"Avto javob xatosi ({uid}): {exc}")

    @client.on(events.NewMessage(pattern=r'^[./](su)$', incoming=False, outgoing=True))
    async def on_start_utag(event):
        if event.chat_id is None:
            return
        # Avvalgi taskni bekor qil
        if uid in _utag_tasks and not _utag_tasks[uid].done():
            _utag_tasks[uid].cancel()
            await asyncio.sleep(0.5)
        task = asyncio.create_task(do_utag(client, uid, event, random_mode=False))
        _utag_tasks[uid] = task
        try:
            await event.delete()
        except Exception:
            pass

    @client.on(events.NewMessage(pattern=r'^[./](ru)$', incoming=False, outgoing=True))
    async def on_start_random_utag(event):
        """.ru yoki /ru — har bir userga random so'z va sticker bilan uTag."""
        if event.chat_id is None:
            return
        if uid in _utag_tasks and not _utag_tasks[uid].done():
            _utag_tasks[uid].cancel()
            await asyncio.sleep(0.5)
        task = asyncio.create_task(do_utag(client, uid, event, random_mode=True))
        _utag_tasks[uid] = task
        try:
            await event.delete()
        except Exception:
            pass

    @client.on(events.NewMessage(pattern=r'^[./](f)$', incoming=False, outgoing=True))
    async def on_stop_utag(event):
        if uid in _utag_tasks and not _utag_tasks[uid].done():
            _utag_tasks[uid].cancel()
        try:
            await event.delete()
        except Exception:
            pass

# ─────────────────────────────────────────────
# AVTO XABAR
# ─────────────────────────────────────────────
@dp.callback_query(F.data == "btn_auto_msg")
async def cb_auto_msg_menu(callback: CallbackQuery, state: FSMContext):
    uid = str(callback.from_user.id)
    if uid not in userbot_clients:
        await callback.answer("❗ Avval akkaunt ulang!", show_alert=True)
        return
    await state.clear()
    await callback.message.edit_text(
        "💠 <b>Avto Xabar</b>\n\nYubormoqchi bo'lgan xabar matnini kiriting:",
        reply_markup=back_kb("main_menu")
    )
    await state.set_state(UserStatesGroup.auto_msg_text)

@dp.message(StateFilter(UserStatesGroup.auto_msg_text), F.text)
async def auto_msg_text_input(message: Message, state: FSMContext):
    await state.update_data(auto_text=message.text)
    await message.answer(
        "📋 Endi foydalanuvchi usernamlarini kiriting (har birini yangi qatordan):\n"
        "Masalan:\n@user1\n@user2",
        reply_markup=back_kb("main_menu")
    )
    await state.set_state(UserStatesGroup.auto_msg_usernames)

@dp.message(StateFilter(UserStatesGroup.auto_msg_usernames), F.text)
async def auto_msg_send(message: Message, state: FSMContext):
    data = await state.get_data()
    text = data.get("auto_text", "")
    uid  = str(message.from_user.id)
    client = userbot_clients.get(uid)
    if not client:
        await message.answer("❌ Akkaunt topilmadi.")
        await state.clear()
        return

    usernames = [u.strip() for u in message.text.split("\n") if u.strip()]
    await message.answer(f"⏳ {len(usernames)} ta foydalanuvchiga xabar yuborilmoqda...")

    sent = 0
    failed = 0
    for uname in usernames:
        try:
            await client.send_message(uname, make_text_unique(text))
            sent += 1
            await asyncio.sleep(2)
        except Exception as e:
            failed += 1
            log.error(f"Xabar yuborishda xato {uname}: {e}")

    await message.answer(
        f"✅ Yuborildi: <b>{sent}</b>\n❌ Muvaffaqiyatsiz: <b>{failed}</b>",
        reply_markup=get_main_keyboard()
    )
    await state.clear()

# ─────────────────────────────────────────────
# AVTO JAVOB
# ─────────────────────────────────────────────
async def get_auto_reply_settings(uid: str) -> tuple[bool, str | None]:
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute(
            "SELECT enabled, response_text FROM auto_reply_settings WHERE owner_id = ?",
            (uid,)
        ) as cur:
            row = await cur.fetchone()
    return bool(row and row[0]), row[1] if row else None


def get_auto_reply_keyboard(enabled: bool) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(
        text="✏️ Javob matnini o'zgartirish",
        callback_data="auto_reply_set"
    ))
    if enabled:
        kb.row(InlineKeyboardButton(
            text="⛔ Avto javobni o'chirish",
            callback_data="auto_reply_disable"
        ))
    kb.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="main_menu"))
    return kb.as_markup()


@dp.callback_query(F.data == "btn_auto_reply")
async def cb_auto_reply_menu(callback: CallbackQuery, state: FSMContext):
    uid = str(callback.from_user.id)
    if uid not in userbot_clients:
        await callback.answer("❗ Avval akkaunt ulang!", show_alert=True)
        return
    await state.clear()
    enabled, response_text = await get_auto_reply_settings(uid)
    status = "🟢 Yoqilgan" if enabled else "🔴 O'chirilgan"
    saved_text = response_text or "Hali javob matni saqlanmagan."
    await callback.message.edit_text(
        "💠 <b>Avto Javob</b>\n\n"
        f"Holati: <b>{status}</b>\n"
        "Akkaunt <b>offline</b> bo'lganda shaxsiy xabarlarga avtomatik javob beradi.\n"
        "Bir odamga 15 daqiqada ko'pi bilan bir marta javob yuboriladi.\n"
        "Oddiy tarifda reklama siz kiritgan matnning tagiga qo'shiladi.\n"
        "PRO tarifda reklama umuman chiqmaydi.\n\n"
        f"<b>Joriy javob:</b>\n{html.escape(saved_text)}",
        reply_markup=get_auto_reply_keyboard(enabled)
    )


@dp.callback_query(F.data == "auto_reply_set")
async def cb_auto_reply_set(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "✏️ Foydalanuvchi sizga yozganda, akkauntingiz offline bo'lsa "
        "yuboriladigan javob matnini kiriting.\n\n"
        "Siz yozgan matn javobning asosiy qismi bo'ladi.\n"
        "Oddiy tarifda uning tagiga avtomatik reklama qo'shiladi.\n"
        "PRO tarifda reklama qo'shilmaydi.",
        reply_markup=back_kb("btn_auto_reply")
    )
    await state.set_state(UserStatesGroup.auto_reply_text)


@dp.message(StateFilter(UserStatesGroup.auto_reply_text), F.text)
async def auto_reply_text_input(message: Message, state: FSMContext):
    response_text = message.text.strip()
    if not response_text:
        await message.answer("❌ Javob matni bo'sh bo'lmasin.")
        return
    uid = str(message.from_user.id)
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(
            "INSERT OR REPLACE INTO auto_reply_settings "
            "(owner_id, enabled, response_text, updated_at) VALUES (?, 1, ?, ?)",
            (uid, response_text, now)
        )
        await db.commit()
    await state.clear()
    await message.answer(
        "✅ Avto javob yoqildi va bazaga saqlandi.\n"
        "Akkauntingiz offline bo'lganda foydalanuvchiga javob yuboriladi.\n"
        "Oddiy tarifda reklama matn tagiga qo'shiladi, PRO tarifda esa reklama chiqmaydi.",
        reply_markup=get_main_keyboard()
    )


@dp.callback_query(F.data == "auto_reply_disable")
async def cb_auto_reply_disable(callback: CallbackQuery):
    uid = str(callback.from_user.id)
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(
            "UPDATE auto_reply_settings SET enabled = 0 WHERE owner_id = ?",
            (uid,)
        )
        await db.commit()
    await callback.answer("⛔ Avto javob o'chirildi.", show_alert=True)
    await callback.message.edit_text(
        "💠 <b>Avto Javob</b>\n\n"
        "Holati: <b>🔴 O'chirilgan</b>\n"
        "Avto javobni qayta yoqish uchun javob matnini saqlang.",
        reply_markup=get_auto_reply_keyboard(False)
    )

# ─────────────────────────────────────────────
# USER YIG'ISH (SCRAPE)
# ─────────────────────────────────────────────
def get_scrape_groups_keyboard(uid: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for key, data in _scrape_group_choices.get(uid, {}).items():
        title = str(data["title"])
        kb.row(InlineKeyboardButton(
            text=f"👥 {title[:42]}",
            callback_data=f"scrape_group:{key}"
        ))
    kb.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="main_menu"))
    return kb.as_markup()


@dp.callback_query(F.data == "btn_scrape")
async def cb_scrape_menu(callback: CallbackQuery, state: FSMContext):
    uid = str(callback.from_user.id)
    client = userbot_clients.get(uid)
    if not client:
        await callback.answer("❗ Avval akkaunt ulang!", show_alert=True)
        return

    await state.clear()
    await callback.message.edit_text("⏳ Akkauntingiz ko'ra oladigan guruhlar olinmoqda...")
    choices: dict[str, dict[str, object]] = {}
    try:
        async for dialog in client.iter_dialogs():
            entity = dialog.entity
            if not dialog.is_group and not (
                dialog.is_channel and getattr(entity, "megagroup", False)
            ):
                continue
            key = str(dialog.id).replace("-", "m")
            choices[key] = {
                "entity": entity,
                "title": dialog.name or str(dialog.id),
            }
            if len(choices) >= 50:
                break
    except Exception as exc:
        log.error(f"Guruhlar ro'yxatini olishda xato ({uid}): {exc}")

    if not choices:
        await callback.message.edit_text(
            "❌ Akkaunt ko'ra oladigan guruh topilmadi.\n\n"
            "Yopiq guruhda akkauntingiz a'zo bo'lishi va xabarlar tarixini "
            "ko'ra olishi kerak.",
            reply_markup=back_kb("main_menu")
        )
        return

    _scrape_group_choices[uid] = choices
    await callback.message.edit_text(
        "💠 <b>User Yig'ish</b>\n\n"
        "Foydalanuvchilarni yig'ish uchun guruhni tugma orqali tanlang.\n"
        "Natija bazaga yoki faylga saqlanmaydi — shu chatga oddiy matn ko'rinishida yuboriladi.",
        reply_markup=get_scrape_groups_keyboard(uid)
    )


@dp.callback_query(F.data.startswith("scrape_group:"))
async def cb_scrape_group_selected(callback: CallbackQuery, state: FSMContext):
    uid = str(callback.from_user.id)
    key = callback.data.split(":", 1)[1]
    choice = _scrape_group_choices.get(uid, {}).get(key)
    if not choice:
        await callback.answer("❌ Guruh tanlovi eskirgan. Qaytadan oching.", show_alert=True)
        return
    await state.update_data(scrape_group_key=key)
    await callback.message.edit_text(
        f"✅ Tanlandi: <b>{html.escape(str(choice['title']))}</b>\n\n"
        "Nechta foydalanuvchi yig'ish kerak? (maksimal 500):",
        reply_markup=back_kb("btn_scrape")
    )
    await state.set_state(UserStatesGroup.scrape_count)


@dp.message(StateFilter(UserStatesGroup.scrape_count), F.text)
async def scrape_count_input(message: Message, state: FSMContext):
    try:
        count = max(1, min(int(message.text.strip()), 500))
    except ValueError:
        await message.answer("❌ Faqat 1 dan 500 gacha raqam kiriting.")
        return

    uid = str(message.from_user.id)
    client = userbot_clients.get(uid)
    data = await state.get_data()
    choice = _scrape_group_choices.get(uid, {}).get(data.get("scrape_group_key", ""))
    if not client or not choice:
        await message.answer("❌ Guruh tanlovi topilmadi. Qaytadan urinib ko'ring.")
        await state.clear()
        return

    group = choice["entity"]
    group_title = str(choice["title"])
    await message.answer(
        f"⏳ <b>{html.escape(group_title)}</b> guruhidagi a'zolar olinmoqda..."
    )

    try:
        me = await client.get_me()
        found: dict[int, tuple[str, str, str]] = {}

        # 1) Avval guruhning haqiqiy a'zolarini olishga harakat qilamiz.
        # Bu usul xabar yozmagan, lekin guruhda bor userlarni ham topadi.
        try:
            async for participant in client.iter_participants(group, limit=None):
                if getattr(participant, "bot", False) or getattr(participant, "deleted", False):
                    continue
                sender_id = getattr(participant, "id", None)
                if not sender_id or sender_id == me.id or sender_id in found:
                    continue
                username = f"@{participant.username}" if getattr(participant, "username", None) else ""
                fullname = get_display_name(participant).replace("\n", " ").strip()
                found[int(sender_id)] = (username, fullname, str(sender_id))
                if len(found) >= count:
                    break
        except Exception as exc:
            log.warning(f"To'liq participant ro'yxatini olish cheklangan ({uid}): {exc}")

        # 2) Agar Telegram guruh a'zolarini to'liq bermasa, xabarlar tarixidan
        # qo'shimcha senderlarni yig'amiz. Bu hech bo'lmaganda yozgan userlarni
        # yo'qotib qo'ymaslik uchun fallback.
        if len(found) < count:
            try:
                async for old_message in client.iter_messages(group, limit=5000):
                    sender = await old_message.get_sender()
                    if not sender or getattr(sender, "bot", False) or getattr(sender, "deleted", False):
                        continue
                    sender_id = getattr(sender, "id", None)
                    if not sender_id or sender_id == me.id or sender_id in found:
                        continue
                    username = f"@{sender.username}" if getattr(sender, "username", None) else ""
                    fullname = get_display_name(sender).replace("\n", " ").strip()
                    found[int(sender_id)] = (username, fullname, str(sender_id))
                    if len(found) >= count:
                        break
            except Exception as exc:
                log.warning(f"Xabarlardan user yig'ish fallback xatosi ({uid}): {exc}")

        # Natijani DB/faylga yubormaymiz — to'g'ridan-to'g'ri BOT CHATIGA
        # oddiy matn ko'rinishida yuboramiz. Username bo'lmasa ham tg:// mention.
        user_lines = []
        for username, fullname, user_id in found.values():
            safe_name = html.escape(fullname or "Foydalanuvchi")
            safe_username = html.escape(username) if username else "—"
            display = f'<a href="tg://user?id={user_id}">{safe_name}</a>'
            user_lines.append(f"{display} | {safe_username} | ID: <code>{user_id}</code>")

        header = (
            f"👥 <b>{html.escape(group_title)}</b> dan yig'ilgan foydalanuvchilar\n"
            f"📊 Jami: <b>{len(user_lines)}</b> ta\n"
            "📋 Ism | Username | ID\n\n"
        )

        if not user_lines:
            await message.answer(
                header + "❌ Foydalanuvchi topilmadi.",
                reply_markup=get_main_keyboard()
            )
        else:
            chunk = header
            for i, user_line in enumerate(user_lines, 1):
                line = f"{i}. {user_line}\n"
                if len(chunk) + len(line) > 3900:
                    await message.answer(chunk)
                    chunk = ""
                chunk += line
            if chunk:
                await message.answer(chunk)

            await message.answer(
                "✅ User yig'ish tugadi. Natija shu chatga matn ko'rinishida yuborildi.\n"
                "ℹ️ Username yo'q userlar ham bosiladigan mention bilan chiqarildi.",
                reply_markup=get_main_keyboard()
            )
    except Exception as exc:
        log.error(f"User yig'ishda xato ({uid}): {exc}")
        await message.answer(
            "❌ Guruh a'zolarini olib bo'lmadi. "
            "Akkaunt guruhga a'zo ekanini va ishtirokchilar ro'yxatini ko'ra olishini tekshiring.",
            reply_markup=get_main_keyboard()
        )
    await state.clear()

# ─────────────────────────────────────────────
# SO'ZLAR MARKETI
# ─────────────────────────────────────────────
def get_word_market_keyboard(packs: list[tuple[int, str, str]]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for pack_id, name, words_json in packs:
        try:
            count = len(__import__("json").loads(words_json))
        except Exception:
            count = 0
        kb.row(InlineKeyboardButton(text=f"📝 {name} ({count} ta)", callback_data=f"market_view:{pack_id}"))
    kb.row(InlineKeyboardButton(text="🗑 Mening eski so'zlarimni o'chirish", callback_data="market_clear"))
    kb.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="main_menu"))
    return kb.as_markup()


@dp.callback_query(F.data == "word_market")
async def cb_word_market(callback: CallbackQuery):
    packs = await get_market_packs()
    current = await get_user_words(str(callback.from_user.id))
    text = "🛒 <b>So'zlar Marketi</b>\n\n"
    text += "Bu yerdan .ru uchun so'zlar to'plamini tanlaysiz. Yangi to'plam tanlansa, eski so'zlaringiz o'chib, yangilari qo'shiladi.\n\n"
    text += f"📌 Hozirgi so'zlaringiz: <b>{len(current)} ta</b>\n\n"
    text += "Kerakli to'plamni tanlang:" if packs else "Hozircha marketda so'zlar yo'q. Admin yangi to'plam qo'shadi."
    await callback.message.edit_text(text, reply_markup=get_word_market_keyboard(packs))


@dp.callback_query(F.data.startswith("market_view:"))
async def cb_market_view(callback: CallbackQuery):
    try:
        pack_id = int(callback.data.split(":", 1)[1])
    except ValueError:
        return
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT name, words FROM word_markets WHERE id = ?", (pack_id,)) as cur:
            row = await cur.fetchone()
    if not row:
        await callback.answer("❌ Market topilmadi", show_alert=True)
        return
    name, words_json = row
    import json
    words = json.loads(words_json)
    preview = "\n".join(f"{i}. {html.escape(w)}" for i, w in enumerate(words[:30], 1))
    if len(words) > 30:
        preview += f"\n... va yana {len(words)-30} ta"
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="✅ Ha, so'zlarni qo'shish", callback_data=f"market_apply:{pack_id}"))
    kb.row(InlineKeyboardButton(text="❌ Yo'q", callback_data="word_market"))
    await callback.message.edit_text(
        f"🛒 <b>{html.escape(name)}</b>\n\n{preview}\n\n<b>Shu so'zlar qo'shilsinmi?</b>",
        reply_markup=kb.as_markup()
    )


@dp.callback_query(F.data.startswith("market_apply:"))
async def cb_market_apply(callback: CallbackQuery):
    try:
        pack_id = int(callback.data.split(":", 1)[1])
    except ValueError:
        return
    import json
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT name, words FROM word_markets WHERE id = ?", (pack_id,)) as cur:
            row = await cur.fetchone()
        if not row:
            await callback.answer("❌ Market topilmadi", show_alert=True)
            return
        name, words_json = row
        words = json.loads(words_json)
        uid = str(callback.from_user.id)
        await db.execute("DELETE FROM user_words WHERE owner_id = ?", (uid,))
        await db.executemany(
            "INSERT OR IGNORE INTO user_words (owner_id, word) VALUES (?, ?)",
            [(uid, w) for w in words]
        )
        await db.commit()
    await callback.answer("✅ So'zlar qo'shildi!", show_alert=True)
    await callback.message.edit_text(
        f"✅ <b>{html.escape(name)}</b> so'zlari qo'shildi.\n\n📌 Jami: <b>{len(words)} ta</b>\n\nEndi .ru yoki /ru qilsangiz shu so'zlardan tasodifiy tanlanadi.",
        reply_markup=back_kb("word_market")
    )


@dp.callback_query(F.data == "market_clear")
async def cb_market_clear(callback: CallbackQuery):
    uid = str(callback.from_user.id)
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("DELETE FROM user_words WHERE owner_id = ?", (uid,))
        await db.commit()
    await callback.answer("🗑 Eski so'zlar o'chirildi!", show_alert=True)
    packs = await get_market_packs()
    await callback.message.edit_text(
        "🛒 <b>So'zlar Marketi</b>\n\n🗑 Eski so'zlaringiz o'chirildi. Endi yangi market tanlashingiz mumkin.",
        reply_markup=get_word_market_keyboard(packs)
    )


# ─────────────────────────────────────────────
# ADMIN PANEL
# ─────────────────────────────────────────────
def get_admin_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="👑 Egasi va adminlar", callback_data="admin_owner"))
    kb.row(InlineKeyboardButton(text="📦 Bot fayllari (.py / .zip)", callback_data="admin_source"))
    kb.row(InlineKeyboardButton(text="📢 Kanallarni boshqarish", callback_data="admin_channels"))
    kb.row(InlineKeyboardButton(text="👥 Foydalanuvchilar", callback_data="admin_users"))
    kb.row(InlineKeyboardButton(text="⭐ PRO berish", callback_data="admin_give_pro"))
    kb.row(InlineKeyboardButton(text="🎉 Konkurs yaratish", callback_data="admin_contest_create"))
    kb.row(InlineKeyboardButton(text="🏆 Aktiv konkurslar", callback_data="admin_contests_list"))
    kb.row(InlineKeyboardButton(text="📣 Xabar tarqatish", callback_data="admin_broadcast"))
    kb.row(InlineKeyboardButton(text="🛒 So'zlar Marketini boshqarish", callback_data="admin_word_market"))
    kb.row(InlineKeyboardButton(text="🧩 Safe Management", callback_data="safe_ext"))
    return kb.as_markup()

def get_admin_channels_keyboard(channels: list[dict]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for ch in channels:
        kb.row(InlineKeyboardButton(
            text=f"🗑 {ch['username']} ni o'chirish",
            callback_data=f"del_channel:{ch['username']}"
        ))
    kb.row(InlineKeyboardButton(text="➕ Kanal qo'shish", callback_data="admin_add_channel"))
    kb.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_panel"))
    return kb.as_markup()

@dp.message(Command("admin"), F.chat.type == "private")
async def cmd_admin(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer(
            "⛔ Sizda admin huquqi yo'q.\n\n"
            f"Telegram ID'ingiz: <code>{message.from_user.id}</code>\n"
            "Admin sifatida qo'shish uchun shu ID'ni loyiha egasiga yuboring."
        )
        return
    await message.answer("🔐 <b>Admin Panel</b>", reply_markup=get_admin_keyboard())


@dp.message(Command("source"), F.chat.type == "private")
@dp.message(Command("files"), F.chat.type == "private")
async def cmd_source(message: Message):
    """Admin uchun kodni .py fayl va ZIP arxiv sifatida yuboradi."""
    if message.from_user.id not in ADMIN_IDS:
        return

    source_path = SOURCE_FILE if os.path.isfile(SOURCE_FILE) else __file__
    if not os.path.isfile(source_path):
        await message.answer("❌ Python fayli topilmadi.")
        return

    # SOURCE_FILE yuklangan .txt bo'lsa ham, Telegramga haqiqiy .py nomida yuboramiz.
    output_dir = os.path.dirname(os.path.abspath(source_path)) or "."
    python_path = os.path.join(output_dir, "pro.tag.10.py")
    generated_python = os.path.abspath(source_path) != os.path.abspath(python_path)
    archive_path = os.path.join(
        output_dir,
        "pro.tag.10_package.zip"
    )
    try:
        if generated_python:
            with open(source_path, "rb") as source_file, open(python_path, "wb") as python_file:
                python_file.write(source_file.read())

        with zipfile.ZipFile(
            archive_path, "w", compression=zipfile.ZIP_DEFLATED
        ) as archive:
            archive.write(python_path, arcname="pro.tag.10.py")
            for support_file in (
                "requirements.txt",
                "Procfile",
                "start.sh",
                ".env.example",
                "HOSTING.md",
            ):
                support_path = os.path.join(output_dir, support_file)
                if os.path.isfile(support_path):
                    archive.write(support_path, arcname=support_file)

        await message.answer_document(
            types.FSInputFile(python_path, filename="pro.tag.10.py"),
            caption="✅ Yangilangan bot kodi (.py)."
        )
        await message.answer_document(
            types.FSInputFile(archive_path, filename="pro.tag.10_package.zip"),
            caption="✅ Bot kodi ZIP arxivda."
        )
    except Exception as exc:
        log.error(f"Source fayl yuborishda xato: {exc}")
        await message.answer("❌ Fayllarni yuborishda xatolik yuz berdi.")
    finally:
        try:
            os.remove(archive_path)
        except OSError:
            pass
        if generated_python:
            try:
                os.remove(python_path)
            except OSError:
                pass


@dp.callback_query(F.data == "admin_source")
async def cb_admin_source(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("🔒 Faqat admin.", show_alert=True)
        return
    await callback.answer("📦 Fayllar tayyorlanmoqda...")
    await cmd_source(callback.message)


@dp.callback_query(F.data == "admin_panel")
async def cb_admin_panel(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    try:
        await callback.message.edit_text("🔐 <b>Admin Panel</b>", reply_markup=get_admin_keyboard())
    except Exception:
        await callback.answer()


@dp.callback_query(F.data == "admin_owner")
async def cb_admin_owner(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    admins = "\n".join(f"• <code>{admin_id}</code>" for admin_id in sorted(ADMIN_IDS))
    await callback.message.edit_text(
        "👑 <b>Bot egasi va adminlar</b>\n\n"
        f"Asosiy egasi: <code>{OWNER_ID}</code>\n\n"
        f"<b>Adminlar:</b>\n{admins}\n\n"
        "Yangi admin qo'shish uchun uning Telegram ID'sini loyiha sozlamalariga qo'shing.",
        reply_markup=back_kb("admin_panel")
    )

# — Kanallar boshqaruvi —
@dp.callback_query(F.data == "admin_channels")
async def cb_admin_channels(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    channels = await get_channels()
    text = "📢 <b>Obuna kanallari</b>\n\n"
    if channels:
        for i, ch in enumerate(channels, 1):
            text += f"{i}. {ch['username']}\n"
    else:
        text += "Hozircha kanallar yo'q."
    await callback.message.edit_text(text, reply_markup=get_admin_channels_keyboard(channels))

@dp.callback_query(F.data == "admin_add_channel")
async def cb_admin_add_channel(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return
    await callback.message.edit_text(
        "➕ Yangi kanal username kiriting (masalan: @my_channel):",
        reply_markup=back_kb("admin_channels")
    )
    await state.set_state(UserStatesGroup.admin_add_channel)

@dp.message(StateFilter(UserStatesGroup.admin_add_channel), F.text)
async def admin_add_channel_input(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return

    raw = normalize_channel_username(message.text)
    if not raw:
        await message.answer("⚠️ Kanal username bo'sh bo'la olmaydi. Iltimos, to'g'ri formatda kiriting, masalan: @my_channel")
        return

    try:
        chat = await bot.get_chat(raw)
    except Exception as exc:
        log.warning("Admin attempted to add invalid channel %s: %s", raw, exc)
        await message.answer(
            f"⚠️ <b>{raw}</b> kanali Telegramda topilmadi. Iltimos, kanalni tekshirib qayta kiriting yoki kanalni ommaviy qilib qo'ying.",
            reply_markup=get_admin_keyboard()
        )
        await state.clear()
        return

    if chat.type not in ("channel", "supergroup", "group"):
        await message.answer(
            f"⚠️ <b>{raw}</b> kanal emas. Faqat kanal/supergroup formatidagi chatlarni qo'shishingiz mumkin.",
            reply_markup=get_admin_keyboard()
        )
        await state.clear()
        return

    url = f"https://t.me/{raw.lstrip('@')}"
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(
            "INSERT OR IGNORE INTO sub_channels VALUES (?, ?, ?)",
            (raw, url, datetime.now(timezone.utc).isoformat())
        )
        await db.commit()
    await state.clear()
    await message.answer(f"✅ <b>{raw}</b> kanali qo'shildi!", reply_markup=get_admin_keyboard())

@dp.callback_query(F.data.startswith("del_channel:"))
async def cb_del_channel(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    ch_username = callback.data.split(":", 1)[1]
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("DELETE FROM sub_channels WHERE channel_username = ?", (ch_username,))
        await db.commit()
    await callback.answer(f"✅ {ch_username} o'chirildi!", show_alert=True)
    channels = await get_channels()
    await callback.message.edit_text(
        "📢 <b>Obuna kanallari</b>",
        reply_markup=get_admin_channels_keyboard(channels)
    )

# — Foydalanuvchilar —
@dp.callback_query(F.data == "admin_users")
async def cb_admin_users(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            total = (await cur.fetchone())[0]
        async with db.execute(
            "SELECT COUNT(*) FROM users WHERE pro_until IS NOT NULL"
        ) as cur:
            pro_count = (await cur.fetchone())[0]
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="📋 Ro'yxat (oxirgi 20)", callback_data="admin_user_list"))
    kb.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_panel"))
    await callback.message.edit_text(
        f"👥 <b>Foydalanuvchilar</b>\n\n"
        f"Jami: <b>{total}</b>\n"
        f"PRO: <b>{pro_count}</b>",
        reply_markup=kb.as_markup()
    )

@dp.callback_query(F.data == "admin_user_list")
async def cb_admin_user_list(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute(
            "SELECT id, fullname, username, pro_until FROM users ORDER BY first_seen DESC LIMIT 20"
        ) as cur:
            rows = await cur.fetchall()
    text = "📋 <b>Oxirgi 20 foydalanuvchi:</b>\n\n"
    for uid, fullname, username, pro_until in rows:
        pro = "✅" if is_pro_user(pro_until) else "❌"
        uname_str = f"@{username}" if username else "—"
        text += f"{pro} <b>{fullname or '?'}</b> ({uname_str}) | ID: <code>{uid}</code>\n"
    await callback.message.edit_text(text, reply_markup=back_kb("admin_users"))

# — PRO berish —
@dp.callback_query(F.data == "admin_give_pro")
async def cb_admin_give_pro_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return
    await callback.message.edit_text(
        "⭐ PRO berish uchun foydalanuvchi ID va kun sonini kiriting:\n"
        "Format: <code>ID kun</code>\nMasalan: <code>123456789 7</code>",
        reply_markup=back_kb("admin_panel")
    )
    await state.set_state(UserStatesGroup.admin_give_pro)

@dp.message(StateFilter(UserStatesGroup.admin_give_pro), F.text)
async def admin_give_pro_input(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    parts = message.text.strip().split()
    if len(parts) != 2:
        await message.answer("❌ Format: <code>ID kun</code>")
        return
    target_id, days_str = parts
    try:
        days = int(days_str)
    except ValueError:
        await message.answer("❌ Kun soni raqam bo'lishi kerak.")
        return

    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT pro_until FROM users WHERE id = ?", (target_id,)) as cur:
            row = await cur.fetchone()
        if not row:
            await message.answer("❌ Foydalanuvchi topilmadi.")
            await state.clear()
            return
        current_pro = row[0]
        base_time = datetime.now(timezone.utc)
        if current_pro and is_pro_user(current_pro):
            base_time = datetime.fromisoformat(current_pro)
        new_pro = (base_time + timedelta(days=days)).isoformat()
        await db.execute(
            "UPDATE users SET pro_until = ?, notified_10m = 0 WHERE id = ?",
            (new_pro, target_id)
        )
        await db.commit()

    # Bio dan reklamani o'chir (agar userbot ulangan bo'lsa)
    if target_id in userbot_clients:
        await set_ad_bio(userbot_clients[target_id], is_pro=True)

    try:
        await bot.send_message(
            int(target_id),
            f"🎉 <b>PRO tarif faollashtirildi!</b>\n\n"
            f"⏳ Muddat: <b>{days} kun</b>\n"
            f"✅ Profil bio'ngizdan reklama olib tashlandi."
        )
    except Exception:
        pass

    await state.clear()
    await message.answer(
        f"✅ Foydalanuvchi <code>{target_id}</code> ga {days} kunlik PRO berildi.",
        reply_markup=get_admin_keyboard()
    )

# — So'zlar Marketi admin boshqaruvi —
def get_admin_market_keyboard(packs: list[tuple[int, str, str]]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for pack_id, name, words_json in packs:
        kb.row(InlineKeyboardButton(text=f"🗑 {name}", callback_data=f"admin_market_del:{pack_id}"))
    kb.row(InlineKeyboardButton(text="➕ Yangi so'zlar to'plami", callback_data="admin_market_add"))
    kb.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_panel"))
    return kb.as_markup()


@dp.callback_query(F.data == "admin_word_market")
async def cb_admin_word_market(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    packs = await get_market_packs()
    text = "🛒 <b>So'zlar Marketini boshqarish</b>\n\n"
    text += "Mavjud to'plamlar:\n" if packs else "Hozircha to'plam yo'q.\n"
    for pack_id, name, words_json in packs:
        import json
        try: count = len(json.loads(words_json))
        except Exception: count = 0
        text += f"• <b>{html.escape(name)}</b> — {count} ta so'z\n"
    await callback.message.edit_text(text, reply_markup=get_admin_market_keyboard(packs))


@dp.callback_query(F.data == "admin_market_add")
async def cb_admin_market_add(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return
    await callback.message.edit_text(
        "➕ <b>Yangi so'zlar to'plami</b>\n\nAvval market nomini yuboring.\nMasalan: <code>Sayfiddinov so'zlari</code>",
        reply_markup=back_kb("admin_word_market")
    )
    await state.set_state(UserStatesGroup.admin_market_name)


@dp.message(StateFilter(UserStatesGroup.admin_market_name), F.text)
async def admin_market_name_input(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    name = message.text.strip()[:100]
    if not name:
        await message.answer("❌ Market nomi bo'sh bo'lmasin.")
        return
    await state.update_data(market_name=name)
    await message.answer(
        "📝 Endi so'zlarni yuboring. Har bir so'zni alohida qatorda yozing.\n\n"
        "Masalan:\n<code>qahramon\nshirincha\nkayfiyat</code>",
        reply_markup=back_kb("admin_word_market")
    )
    await state.set_state(UserStatesGroup.admin_market_words)


@dp.message(StateFilter(UserStatesGroup.admin_market_words), F.text)
async def admin_market_words_input(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    import json
    words = parse_market_words(message.text)
    if not words:
        await message.answer("❌ Hech qanday so'z topilmadi. Qaytadan yuboring.")
        return
    data = await state.get_data()
    name = data.get("market_name", "Yangi to'plam")
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(
            "INSERT OR REPLACE INTO word_markets (name, words, created_at) VALUES (?, ?, ?)",
            (name, json.dumps(words, ensure_ascii=False), datetime.now(timezone.utc).isoformat())
        )
        await db.commit()
    await state.clear()
    await message.answer(
        f"✅ <b>{html.escape(name)}</b> marketi qo'shildi.\n📌 So'zlar: <b>{len(words)} ta</b>",
        reply_markup=get_admin_keyboard()
    )


@dp.callback_query(F.data.startswith("admin_market_del:"))
async def cb_admin_market_del(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    try:
        pack_id = int(callback.data.split(":", 1)[1])
    except ValueError:
        return
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("DELETE FROM word_markets WHERE id = ?", (pack_id,))
        await db.commit()
    await callback.answer("🗑 Market o'chirildi!", show_alert=True)
    packs = await get_market_packs()
    await callback.message.edit_text(
        "🛒 <b>So'zlar Marketini boshqarish</b>",
        reply_markup=get_admin_market_keyboard(packs)
    )

# — Xabar tarqatish —
@dp.callback_query(F.data == "admin_broadcast")
async def cb_admin_broadcast(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return
    await callback.message.edit_text(
        "📣 Barcha foydalanuvchilarga yuboriladigan xabarni kiriting:",
        reply_markup=back_kb("admin_panel")
    )
    await state.set_state(UserStatesGroup.admin_broadcast)

@dp.message(StateFilter(UserStatesGroup.admin_broadcast), F.text)
async def admin_broadcast_send(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    text = message.text
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT id FROM users") as cur:
            user_ids = [r[0] for r in await cur.fetchall()]

    sent = 0
    failed = 0
    for uid in user_ids:
        try:
            await bot.send_message(int(uid), text)
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1

    await state.clear()
    await message.answer(
        f"📣 Xabar yuborildi!\n✅ Muvaffaqiyatli: <b>{sent}</b>\n❌ Muvaffaqiyatsiz: <b>{failed}</b>",
        reply_markup=get_admin_keyboard()
    )

# ─────────────────────────────────────────────
# KONKURS (GIVEAWAY)
# ─────────────────────────────────────────────

# ── Admin: konkurs yaratish ──
@dp.callback_query(F.data == "admin_contest_create")
async def cb_contest_create(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return
    await state.clear()
    await callback.message.edit_text(
        "🎉 <b>Konkurs yaratish</b>\n\n"
        "1️⃣ Konkurs o'tkaziladigan kanal yoki guruh username ini kiriting:\n"
        "(masalan: <code>@mening_kanalim</code>)",
        reply_markup=back_kb("admin_panel")
    )
    await state.set_state(UserStatesGroup.contest_channel)

@dp.message(StateFilter(UserStatesGroup.contest_channel), F.text)
async def contest_channel_input(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    raw = message.text.strip()
    if not raw.startswith("@"):
        raw = "@" + raw
    await state.update_data(contest_channel=raw)
    await message.answer(
        "2️⃣ Nechta ishtirokchi to'lganda g'olib tanlansin?\n"
        "(masalan: <code>100</code>)"
    )
    await state.set_state(UserStatesGroup.contest_max_users)

@dp.message(StateFilter(UserStatesGroup.contest_max_users), F.text)
async def contest_max_input(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    try:
        max_u = int(message.text.strip())
        if max_u < 1:
            raise ValueError
    except ValueError:
        await message.answer("❌ Faqat musbat raqam kiriting.")
        return
    await state.update_data(contest_max=max_u)
    await message.answer(
        "3️⃣ Ishtirok etish uchun majburiy kanallar/guruhlar username larini kiriting.\n"
        "Har birini yangi qatordan yozing. Majburiy kanal bo'lmasa <code>yo'q</code> yozing.\n\n"
        "Masalan:\n<code>@kanal1\n@kanal2</code>"
    )
    await state.set_state(UserStatesGroup.contest_req_channels)

@dp.message(StateFilter(UserStatesGroup.contest_req_channels), F.text)
async def contest_req_ch_input(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    text = message.text.strip()
    if text.lower() in ("yo'q", "yoq", "no", "-"):
        req_channels = []
    else:
        req_channels = [c.strip() if c.strip().startswith("@") else "@" + c.strip()
                        for c in text.split("\n") if c.strip()]
    await state.update_data(contest_req_channels=req_channels)
    await message.answer(
        "4️⃣ Sovrin matnini kiriting (konkurs xabarida ko'rinadi):\n\n"
        "Masalan: <i>G'olib 500,000 so'm pul mukofoti oladi!</i>"
    )
    await state.set_state(UserStatesGroup.contest_prize_text)

@dp.message(StateFilter(UserStatesGroup.contest_prize_text), F.text)
async def contest_prize_input(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    data = await state.get_data()
    channel     = data["contest_channel"]
    max_u       = data["contest_max"]
    req_ch_list = data.get("contest_req_channels", [])
    prize_text  = message.text.strip()
    req_ch_str  = ",".join(req_ch_list) if req_ch_list else ""

    # Konkurs xabarini kanalga yubor
    req_ch_display = "\n".join(f"• {c}" for c in req_ch_list) if req_ch_list else "Yo'q"
    contest_text = (
        f"🎉 <b>KONKURS BOSHLANDI!</b>\n\n"
        f"🏆 Sovrin: {prize_text}\n\n"
        f"👥 Kerakli ishtirokchilar soni: <b>{max_u}</b>\n"
        f"📢 Majburiy kanallar:\n{req_ch_display}\n\n"
        f"✅ Ishtirok etish uchun pastdagi tugmani bosing!"
    )

    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="🎟 Ishtirok etish", callback_data="join_contest_PLACEHOLDER"))

    # Avval bot kanalda bor-yo'qligini tekshiramiz
    try:
        chat = await bot.get_chat(channel)
        real_chat_id = str(chat.id)
    except Exception as e:
        await state.clear()
        await message.answer(
            f"❌ Kanal topilmadi: <code>{e}</code>\n\n"
            "Tekshiring:\n"
            "• Username to'g'rimi? (masalan: <code>@kanalim</code>)\n"
            "• Bot kanalda member sifatida bormi?",
            reply_markup=get_admin_keyboard()
        )
        return

    # Kanalga xabar yuborish
    try:
        sent = await bot.send_message(real_chat_id, contest_text, reply_markup=kb.as_markup())
        message_id = str(sent.message_id)

        # DB ga saqlash
        async with aiosqlite.connect(DB_FILE) as db:
            cur = await db.execute(
                "INSERT INTO contests (chat_id, message_id, prize_text, max_users, req_channels, status, created_at) "
                "VALUES (?, ?, ?, ?, ?, 'active', ?)",
                (real_chat_id, message_id, prize_text, max_u, req_ch_str,
                 datetime.now(timezone.utc).isoformat())
            )
            contest_id = cur.lastrowid
            await db.commit()

        # Tugmani contest_id bilan yangilash
        kb2 = InlineKeyboardBuilder()
        kb2.row(InlineKeyboardButton(
            text="🎟 Ishtirok etish",
            callback_data=f"join_contest:{contest_id}"
        ))
        await bot.edit_message_reply_markup(
            chat_id=real_chat_id,
            message_id=int(message_id),
            reply_markup=kb2.as_markup()
        )

        await state.clear()
        await message.answer(
            f"✅ Konkurs #{contest_id} <b>{channel}</b> kanaliga yuborildi!\n\n"
            f"👥 Kerakli: {max_u} ishtirokchi\n"
            f"🏆 Sovrin: {prize_text}",
            reply_markup=get_admin_keyboard()
        )
    except Exception as e:
        await state.clear()
        await message.answer(
            f"❌ Kanalga xabar yuborib bo'lmadi!\n\n"
            f"Telegram xatosi: <code>{e}</code>\n\n"
            "Tekshiring:\n"
            "• Bot kanalda <b>admin</b> sifatida qo'shilganmi?\n"
            "• Adminga <b>«Xabar yuborish»</b> ruxsati berilganmi?\n"
            "• Kanal shaxsiy (private) bo'lsa, username emas, ID kerak",
            reply_markup=get_admin_keyboard()
        )

# ── Admin: aktiv konkurslar ro'yxati ──
@dp.callback_query(F.data == "admin_contests_list")
async def cb_admin_contests(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute(
            "SELECT id, chat_id, prize_text, max_users, status, "
            "(SELECT COUNT(*) FROM contest_participants WHERE contest_id = contests.id) as cnt "
            "FROM contests ORDER BY id DESC LIMIT 10"
        ) as cur:
            rows = await cur.fetchall()

    if not rows:
        await callback.message.edit_text(
            "Hech qanday konkurs yo'q.", reply_markup=back_kb("admin_panel")
        )
        return

    kb = InlineKeyboardBuilder()
    text = "🏆 <b>Konkurslar (oxirgi 10)</b>\n\n"
    for cid, chat_id, prize, max_u, status, cnt in rows:
        emoji = "🟢" if status == "active" else "🔴"
        text += f"{emoji} #{cid} | {chat_id}\n   {prize[:30]}...\n   👥 {cnt}/{max_u}\n\n"
        if status == "active":
            kb.row(
                InlineKeyboardButton(text=f"🏆 #{cid} g'olibni tanlash", callback_data=f"contest_finish:{cid}"),
                InlineKeyboardButton(text=f"❌ #{cid} bekor", callback_data=f"contest_cancel:{cid}")
            )
    kb.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_panel"))
    await callback.message.edit_text(text, reply_markup=kb.as_markup())

# ── Admin: g'olibni qo'lda tanlash ──
@dp.callback_query(F.data.startswith("contest_finish:"))
async def cb_contest_finish(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    contest_id = int(callback.data.split(":")[1])
    await pick_winner(contest_id)
    await callback.answer("✅ G'olib tanlandi!", show_alert=True)
    # Ro'yxatni yangilash
    await cb_admin_contests(callback)

# ── Admin: konkursni bekor qilish ──
@dp.callback_query(F.data.startswith("contest_cancel:"))
async def cb_contest_cancel(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    contest_id = int(callback.data.split(":")[1])
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(
            "UPDATE contests SET status = 'cancelled' WHERE id = ?", (contest_id,)
        )
        await db.commit()
    await callback.answer("❌ Konkurs bekor qilindi!", show_alert=True)
    await cb_admin_contests(callback)

# ── User: konkursga ishtirok etish ──
@dp.callback_query(F.data.startswith("join_contest:"))
async def cb_join_contest(callback: CallbackQuery):
    contest_id = int(callback.data.split(":")[1])
    user_id    = str(callback.from_user.id)

    async with aiosqlite.connect(DB_FILE) as db:
        # Konkurs mavjudligini tekshirish
        async with db.execute(
            "SELECT max_users, req_channels, status, prize_text, chat_id, message_id "
            "FROM contests WHERE id = ?", (contest_id,)
        ) as cur:
            row = await cur.fetchone()

        if not row:
            await callback.answer("❌ Konkurs topilmadi!", show_alert=True)
            return

        max_u, req_ch_str, status, prize_text, chat_id, message_id = row

        if status != "active":
            await callback.answer("❌ Bu konkurs yakunlangan!", show_alert=True)
            return

        # Allaqachon ishtirok etganmi?
        async with db.execute(
            "SELECT 1 FROM contest_participants WHERE contest_id = ? AND user_id = ?",
            (contest_id, user_id)
        ) as cur:
            already = await cur.fetchone()

        if already:
            await callback.answer("✅ Siz allaqachon ishtirok etgansiz!", show_alert=True)
            return

    # Majburiy kanallarga obunani tekshirish
    req_channels = [c for c in req_ch_str.split(",") if c] if req_ch_str else []
    not_joined = []
    for ch in req_channels:
        try:
            member = await bot.get_chat_member(chat_id=ch, user_id=int(user_id))
            if member.status in ["left", "kicked"]:
                not_joined.append(ch)
        except Exception:
            not_joined.append(ch)

    if not_joined:
        kb = InlineKeyboardBuilder()
        for ch in not_joined:
            url = f"https://t.me/{ch.lstrip('@')}"
            kb.row(InlineKeyboardButton(text=f"📢 {ch} ga a'zo bo'lish", url=url))
        kb.row(InlineKeyboardButton(
            text="✅ Obunani tekshirish",
            callback_data=f"join_contest:{contest_id}"
        ))
        await callback.answer("❌ Avval majburiy kanallarga a'zo bo'ling!", show_alert=True)
        try:
            await bot.send_message(
                callback.from_user.id,
                "⚠️ Konkursga ishtirok etish uchun quyidagi kanallarga a'zo bo'ling:",
                reply_markup=kb.as_markup()
            )
        except Exception:
            pass
        return

    # Ishtirokchini qo'shish
    fullname = callback.from_user.full_name or ""
    username = f"@{callback.from_user.username}" if callback.from_user.username else fullname

    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(
            "INSERT OR IGNORE INTO contest_participants (contest_id, user_id, username, fullname, joined_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (contest_id, user_id, username, fullname, datetime.now(timezone.utc).isoformat())
        )
        await db.commit()

        # Joriy son
        async with db.execute(
            "SELECT COUNT(*) FROM contest_participants WHERE contest_id = ?", (contest_id,)
        ) as cur:
            cnt = (await cur.fetchone())[0]

    await callback.answer(
        f"🎟 Ishtirok etdingiz! Siz {cnt}-ishtirokchisiz.", show_alert=True
    )

    # Xabardagi tugma matnini yangilaymiz
    try:
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(
            text=f"🎟 Ishtirok etish ({cnt}/{max_u})",
            callback_data=f"join_contest:{contest_id}"
        ))
        await bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=int(message_id),
            reply_markup=kb.as_markup()
        )
    except Exception:
        pass

    # Kerakli son to'ldimi? → g'olib tanlash
    if cnt >= max_u:
        await pick_winner(contest_id)

# ── G'olib tanlash ──
async def pick_winner(contest_id: int):
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute(
            "SELECT status, chat_id, message_id, prize_text "
            "FROM contests WHERE id = ?", (contest_id,)
        ) as cur:
            row = await cur.fetchone()

        if not row or row[0] != "active":
            return

        _, chat_id, message_id, prize_text = row

        async with db.execute(
            "SELECT user_id, username, fullname "
            "FROM contest_participants WHERE contest_id = ?", (contest_id,)
        ) as cur:
            participants = await cur.fetchall()

        if not participants:
            return

        winner = random.choice(participants)
        winner_id, winner_username, winner_fullname = winner
        winner_display = winner_username if winner_username.startswith("@") else winner_fullname

        await db.execute(
            "UPDATE contests SET status = 'finished', winner_id = ? WHERE id = ?",
            (winner_id, contest_id)
        )
        await db.commit()

    # Kanalga g'olib e'loni
    total = len(participants)
    announce = (
        f"🏆 <b>KONKURS YAKUNLANDI!</b>\n\n"
        f"🎉 G'olib: <b>{winner_display}</b>\n"
        f"🏅 Sovrin: {prize_text}\n\n"
        f"👥 Jami ishtirokchilar: {total} ta\n\n"
        f"Tabriklaymiz! 🎊"
    )
    try:
        await bot.send_message(chat_id, announce)
    except Exception as e:
        log.error(f"G'olib e'lonida xato: {e}")

    # G'olibga shaxsiy xabar
    try:
        await bot.send_message(
            int(winner_id),
            f"🎉 <b>Tabriklaymiz!</b>\n\n"
            f"Siz konkursda g'olib bo'ldingiz!\n"
            f"🏅 Sovrin: {prize_text}\n\n"
            f"Mukofotni olish uchun {ADMIN_CONTACT_TEXT} ga murojaat qiling."
        )
    except Exception:
        pass

    # Adminga xabar
    try:
        await bot.send_message(
            ADMIN_ID,
            f"🏆 <b>Konkurs #{contest_id} yakunlandi!</b>\n\n"
            f"G'olib: {winner_display}\n"
            f"ID: <code>{winner_id}</code>\n"
            f"Jami ishtirokchilar: {total}"
        )
    except Exception:
        pass


# ─────────────────────────────────────────────
# 💬 PM SAFE MESSAGE
# ─────────────────────────────────────────────
_pm_tasks: dict[str, asyncio.Task] = {}
_pm_stop_events: dict[str, asyncio.Event] = {}

def is_pm_admin(uid: int) -> bool:
    return uid in ADMIN_IDS

async def is_pm_allowed(uid: int) -> bool:
    if is_pm_admin(uid):
        return True
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT pro_until FROM users WHERE id = ?", (str(uid),)) as cur:
            row = await cur.fetchone()
    return bool(row and is_pro_user(row[0]))

async def get_pm_recipient_count() -> int:
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM users u JOIN pm_preferences p ON p.user_id=u.id "
            "WHERE p.consent=1 AND p.unsubscribed=0"
        ) as cur:
            return int((await cur.fetchone())[0])

async def get_pm_user_status(uid: int) -> tuple[bool, bool]:
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute(
            "SELECT consent, unsubscribed FROM pm_preferences WHERE user_id=?",
            (str(uid),)
        ) as cur:
            row = await cur.fetchone()
    return (bool(row[0]), bool(row[1])) if row else (False, False)

def pm_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="📝 Xabar yuborish", callback_data="pm_content_menu"),
        InlineKeyboardButton(text="👥 Qabul qiluvchilar", callback_data="pm_recipients")
    )
    kb.row(
        InlineKeyboardButton(text="⚡ Limit/tezlik", callback_data="pm_rate"),
        InlineKeyboardButton(text="📊 Natija", callback_data="pm_result")
    )
    kb.row(
        InlineKeyboardButton(text="▶️ Boshlash", callback_data="pm_start"),
        InlineKeyboardButton(text="⏹️ Stop", callback_data="pm_stop")
    )
    kb.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="main_menu"))
    return kb.as_markup()

def pm_content_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="💬 SMS", callback_data="pm_type:text"),
        InlineKeyboardButton(text="😀 Emoji", callback_data="pm_type:emoji")
    )
    kb.row(
        InlineKeyboardButton(text="🎞️ GIF", callback_data="pm_type:gif"),
        InlineKeyboardButton(text="🖼️ Sticker", callback_data="pm_type:sticker")
    )
    kb.row(InlineKeyboardButton(text="🔀 Aralash", callback_data="pm_type:mixed"))
    kb.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="pm_safe"))
    return kb.as_markup()

def pm_confirm_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="✅ Ha", callback_data="pm_confirm"),
        InlineKeyboardButton(text="❌ Yo'q", callback_data="pm_safe")
    )
    return kb.as_markup()

async def pm_rate_seconds() -> float:
    # Konservativ interval; Telegram limitlarini aylanib o'tish yo'q.
    return 2.0

async def pm_load_content(uid: int) -> list[dict]:
    import json
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute(
            "SELECT content_json FROM pm_drafts WHERE owner_id=?", (str(uid),)
        ) as cur:
            row = await cur.fetchone()
    if not row:
        return []
    try:
        return json.loads(row[0])
    except Exception:
        return []

async def pm_save_content(uid: int, items: list[dict], content_type: str):
    import json
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(
            "INSERT OR REPLACE INTO pm_drafts(owner_id,content_type,content_json,updated_at) "
            "VALUES (?,?,?,?)",
            (str(uid), content_type, json.dumps(items, ensure_ascii=False),
             datetime.now(timezone.utc).isoformat())
        )
        await db.commit()

async def pm_get_last_campaign(uid: int):
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute(
            "SELECT id, status, total, success, skipped, failed, stopped, unsubscribed, "
            "started_at, finished_at FROM pm_campaigns WHERE owner_id=? ORDER BY id DESC LIMIT 1",
            (str(uid),)
        ) as cur:
            return await cur.fetchone()

async def pm_send_item(user_id: int, item: dict):
    markup = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="❌ Xabarlarni to'xtatish", callback_data="pm_unsub")
    ]])
    kind, value = item.get("type"), item.get("value")
    if kind in ("text", "emoji"):
        await bot.send_message(int(user_id), value, reply_markup=markup)
    elif kind == "gif":
        await bot.send_animation(int(user_id), value, reply_markup=markup)
    elif kind == "sticker":
        await bot.send_sticker(int(user_id), value)
    else:
        raise ValueError("Noma'lum kontent turi")

async def pm_run_campaign(owner_id: int, campaign_id: int):
    owner_key = str(owner_id)
    stop_event = _pm_stop_events.setdefault(owner_key, asyncio.Event())
    stop_event.clear()
    success = skipped = failed = unsub_count = 0
    started = datetime.now(timezone.utc).isoformat()

    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(
            "UPDATE pm_campaigns SET status='running', started_at=? WHERE id=?",
            (started, campaign_id)
        )
        await db.commit()
        async with db.execute(
            "SELECT content_json FROM pm_campaigns WHERE id=?", (campaign_id,)
        ) as cur:
            row = await cur.fetchone()
        async with db.execute(
            "SELECT u.id FROM users u JOIN pm_preferences p ON p.user_id=u.id "
            "WHERE p.consent=1 AND p.unsubscribed=0 ORDER BY u.id"
        ) as cur:
            recipients = [r[0] for r in await cur.fetchall()]

    import json
    items = json.loads(row[0]) if row else []
    total = len(recipients)
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("UPDATE pm_campaigns SET total=? WHERE id=?", (total, campaign_id))
        await db.commit()

    delay = await pm_rate_seconds()
    consecutive_errors = 0

    for recipient in recipients:
        if stop_event.is_set():
            break
        consent, unsub = await get_pm_user_status(int(recipient))
        if not consent or unsub:
            skipped += 1
            continue

        status = "failed"
        err_text = None
        try:
            for item in items:
                if stop_event.is_set():
                    break
                await pm_send_item(recipient, item)
                await asyncio.sleep(delay)

            if stop_event.is_set():
                status = "stopped"
            else:
                success += 1
                consecutive_errors = 0
                status = "success"

        except TelegramRetryAfter as e:
            # Flood-limit qaytsa chetlab o'tmaymiz: kampaniya avtomatik to'xtaydi.
            stop_event.set()
            failed += 1
            err_text = f"Telegram flood-limit: {e}"
            status = "stopped_flood_limit"

        except TelegramForbiddenError as e:
            # Bot bloklangan/yuborish taqiqlangan userni ro'yxatdan chiqaramiz.
            async with aiosqlite.connect(DB_FILE) as db:
                await db.execute(
                    "UPDATE pm_preferences SET unsubscribed=1, updated_at=? WHERE user_id=?",
                    (datetime.now(timezone.utc).isoformat(), str(recipient))
                )
                await db.commit()
            unsub_count += 1
            skipped += 1
            status = "unsubscribed_or_blocked"
            err_text = str(e)

        except Exception as e:
            failed += 1
            consecutive_errors += 1
            err_text = str(e)[:300]
            status = "failed"
            if consecutive_errors >= 5:
                stop_event.set()

        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute(
                "INSERT INTO pm_campaign_results "
                "(campaign_id,user_id,status,error,created_at) VALUES (?,?,?,?,?)",
                (campaign_id, str(recipient), status, err_text,
                 datetime.now(timezone.utc).isoformat())
            )
            await db.execute(
                "UPDATE pm_campaigns SET success=?, skipped=?, failed=?, unsubscribed=?, stopped=? WHERE id=?",
                (success, skipped, failed, unsub_count, int(stop_event.is_set()), campaign_id)
            )
            await db.commit()

        if stop_event.is_set():
            break

    finished = datetime.now(timezone.utc).isoformat()
    final_status = "stopped" if stop_event.is_set() else "finished"
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(
            "UPDATE pm_campaigns SET status=?, finished_at=?, success=?, skipped=?, failed=?, "
            "unsubscribed=?, stopped=? WHERE id=?",
            (final_status, finished, success, skipped, failed, unsub_count,
             int(stop_event.is_set()), campaign_id)
        )
        await db.commit()

    _pm_tasks.pop(owner_key, None)
    try:
        await bot.send_message(
            owner_id,
            f"📊 <b>PM natijasi #{campaign_id}</b>\n\n"
            f"✅ Muvaffaqiyatli: {success}\n"
            f"⏭️ O'tkazib yuborildi: {skipped}\n"
            f"❌ Xatolik: {failed}\n"
            f"🚫 Unsubscribe/bloklagan: {unsub_count}\n"
            f"⏹️ To'xtatilgan: {'Ha' if stop_event.is_set() else 'Yo‘q'}",
            reply_markup=pm_keyboard()
        )
    except Exception:
        pass

@dp.callback_query(F.data == "pm_safe")
async def cb_pm_safe(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    if not await is_pm_allowed(callback.from_user.id):
        await callback.answer("🔒 Faqat Owner, Super Admin yoki ruxsat berilgan VIP.", show_alert=True)
        return
    count = await get_pm_recipient_count()
    await callback.message.edit_text(
        "💬 <b>PM Safe Message</b>\n\n"
        f"👥 Xavfsiz qabul qiluvchilar: <b>{count}</b>\n\n"
        "Faqat bot bilan muloqot qilgan/rozilik bergan va unsubscribe qilmagan userlar ishlatiladi.\n"
        "⚠️ Flood-limit, bloklash yoki ko'p xatolik bo'lsa avtomatik to'xtaydi.",
        reply_markup=pm_keyboard()
    )

@dp.callback_query(F.data == "pm_content_menu")
async def cb_pm_content_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("📝 <b>Kontent turini tanlang:</b>", reply_markup=pm_content_keyboard())

@dp.callback_query(F.data.startswith("pm_type:"))
async def cb_pm_type(callback: CallbackQuery, state: FSMContext):
    kind = callback.data.split(":", 1)[1]
    await state.update_data(pm_items=[], pm_content_type=kind)
    await state.set_state(
        UserStatesGroup.pm_mixed_content if kind == "mixed" else UserStatesGroup.pm_content
    )
    prompt = {
        "text": "💬 SMS matnini yuboring.",
        "emoji": "😀 Emoji yoki emoji bilan matn yuboring.",
        "gif": "🎞️ GIF yuboring.",
        "sticker": "🖼️ Sticker yuboring.",
        "mixed": "🔀 Aralash: matn, GIF yoki sticker yuboring. Tugagach «✅ Tayyor» ni bosing."
    }[kind]
    kb = InlineKeyboardBuilder()
    if kind == "mixed":
        kb.row(InlineKeyboardButton(text="✅ Tayyor", callback_data="pm_mixed_done"))
    kb.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="pm_safe"))
    await callback.message.edit_text(prompt, reply_markup=kb.as_markup())

@dp.message(StateFilter(UserStatesGroup.pm_content))
async def pm_content_input(message: Message, state: FSMContext):
    data = await state.get_data()
    kind = data.get("pm_content_type")
    item = None
    if kind in ("text", "emoji") and message.text:
        item = {"type": kind, "value": message.text.strip()}
    elif kind == "gif" and message.animation:
        item = {"type": "gif", "value": message.animation.file_id}
    elif kind == "sticker" and message.sticker:
        item = {"type": "sticker", "value": message.sticker.file_id}
    else:
        await message.answer("❌ Tanlangan kontent turiga mos xabar yuboring.")
        return

    await pm_save_content(message.from_user.id, [item], kind)
    await state.clear()
    await message.answer("✅ Kontent saqlandi.", reply_markup=pm_keyboard())

@dp.message(StateFilter(UserStatesGroup.pm_mixed_content))
async def pm_mixed_input(message: Message, state: FSMContext):
    data = await state.get_data()
    items = list(data.get("pm_items", []))

    if message.text:
        items.append({"type": "text", "value": message.text.strip()})
    elif message.animation:
        items.append({"type": "gif", "value": message.animation.file_id})
    elif message.sticker:
        items.append({"type": "sticker", "value": message.sticker.file_id})
    else:
        await message.answer("❌ Faqat matn, GIF yoki sticker qo'shish mumkin.")
        return

    if len(items) > 10:
        await message.answer("⚠️ Maksimal 10 ta kontent.")
        return

    await state.update_data(pm_items=items)
    await message.answer(f"➕ Qo'shildi. Jami: {len(items)} ta.")

@dp.callback_query(F.data == "pm_mixed_done")
async def cb_pm_mixed_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    items = data.get("pm_items", [])
    if not items:
        await callback.answer("Avval kontent yuboring.", show_alert=True)
        return

    await pm_save_content(callback.from_user.id, items, "mixed")
    await state.clear()
    await callback.message.edit_text(
        f"🔀 <b>Aralash kontent saqlandi:</b> {len(items)} ta",
        reply_markup=pm_keyboard()
    )

@dp.callback_query(F.data == "pm_recipients")
async def cb_pm_recipients(callback: CallbackQuery):
    count = await get_pm_recipient_count()
    await callback.message.edit_text(
        f"👥 <b>Qabul qiluvchilar</b>\n\n"
        f"🟢 Xavfsiz ro'yxat: <b>{count}</b>\n"
        "Ruxsatsiz Telegram IDlariga yuborish mavjud emas.",
        reply_markup=pm_keyboard()
    )

@dp.callback_query(F.data == "pm_rate")
async def cb_pm_rate(callback: CallbackQuery):
    await callback.message.edit_text(
        "⚡ <b>Limit/tezlik</b>\n\n"
        "Xavfsiz interval: <b>2 soniya</b>.\n"
        "Flood-limit qaytsa kampaniya darhol to'xtaydi.",
        reply_markup=pm_keyboard()
    )

@dp.callback_query(F.data == "pm_start")
async def cb_pm_start(callback: CallbackQuery):
    if not await is_pm_allowed(callback.from_user.id):
        await callback.answer("🔒 Ruxsat yo'q.", show_alert=True)
        return

    uid = str(callback.from_user.id)
    if uid in _pm_tasks and not _pm_tasks[uid].done():
        await callback.answer("⚠️ Kampaniya allaqachon ishlayapti.", show_alert=True)
        return

    items = await pm_load_content(callback.from_user.id)
    count = await get_pm_recipient_count()
    if not items:
        await callback.answer("Avval kontent tayyorlang.", show_alert=True)
        return
    if count == 0:
        await callback.answer("❌ Qabul qiluvchilar yo'q.", show_alert=True)
        return

    await callback.message.edit_text(
        "⚠️ <b>DIQQAT</b>\n\n"
        f"Xabar faqat rozilik bergan <b>{count}</b> userga yuboriladi.\n"
        "Flood-limit yoki ko'p xatolik bo'lsa avtomatik to'xtaydi.\n\n"
        "Davom etilsinmi?",
        reply_markup=pm_confirm_keyboard()
    )

@dp.callback_query(F.data == "pm_confirm")
async def cb_pm_confirm(callback: CallbackQuery):
    if not await is_pm_allowed(callback.from_user.id):
        await callback.answer("🔒 Ruxsat yo'q.", show_alert=True)
        return

    uid = str(callback.from_user.id)
    if uid in _pm_tasks and not _pm_tasks[uid].done():
        await callback.answer("⚠️ Kampaniya allaqachon ishlayapti.", show_alert=True)
        return

    items = await pm_load_content(callback.from_user.id)
    if not items:
        await callback.answer("❌ Kontent topilmadi.", show_alert=True)
        return

    import json
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(DB_FILE) as db:
        cur = await db.execute(
            "INSERT INTO pm_campaigns "
            "(owner_id,content_type,content_json,status,created_at) VALUES (?,?,?,?,?)",
            (
                uid,
                "mixed" if len(items) > 1 else items[0]["type"],
                json.dumps(items, ensure_ascii=False),
                "queued",
                now,
            )
        )
        campaign_id = cur.lastrowid
        await db.commit()

    task = asyncio.create_task(pm_run_campaign(callback.from_user.id, campaign_id))
    _pm_tasks[uid] = task

    await callback.answer("🚀 Yuborish boshlandi")
    await callback.message.edit_text(
        f"🚀 <b>Yuborish boshlandi</b>\n\nKampaniya: <b>#{campaign_id}</b>",
        reply_markup=pm_keyboard()
    )

@dp.callback_query(F.data == "pm_stop")
async def cb_pm_stop(callback: CallbackQuery):
    uid = str(callback.from_user.id)
    task = _pm_tasks.get(uid)
    if not task or task.done():
        await callback.answer("ℹ️ Faol kampaniya yo'q.", show_alert=True)
        return

    _pm_stop_events.setdefault(uid, asyncio.Event()).set()
    await callback.answer("⏹️ Stop berildi. Pending yuborishlar bekor qilinadi.", show_alert=True)

@dp.callback_query(F.data == "pm_result")
async def cb_pm_result(callback: CallbackQuery):
    row = await pm_get_last_campaign(callback.from_user.id)
    if not row:
        await callback.message.edit_text(
            "📊 Hali PM kampaniyasi yo'q.",
            reply_markup=pm_keyboard()
        )
        return

    cid, status, total, success, skipped, failed, stopped, unsub_count, started, finished = row
    await callback.message.edit_text(
        f"📊 <b>PM natijasi #{cid}</b>\n\n"
        f"Holat: <b>{status}</b>\n"
        f"👥 Qabul qiluvchilar: {total}\n"
        f"✅ Muvaffaqiyatli: {success}\n"
        f"⏭️ O'tkazib yuborildi: {skipped}\n"
        f"❌ Xatolik: {failed}\n"
        f"🚫 Unsubscribe/blok: {unsub_count}\n"
        f"⏹️ To'xtatilgan: {'Ha' if stopped else 'Yo‘q'}\n"
        f"🕒 Boshlangan: {started or '—'}\n"
        f"🏁 Tugagan: {finished or '—'}",
        reply_markup=pm_keyboard()
    )

@dp.callback_query(F.data == "pm_unsub")
async def cb_pm_unsub(callback: CallbackQuery):
    uid = str(callback.from_user.id)
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(
            "INSERT INTO pm_preferences(user_id,consent,unsubscribed,updated_at) "
            "VALUES (?,1,1,?) "
            "ON CONFLICT(user_id) DO UPDATE SET unsubscribed=1, updated_at=excluded.updated_at",
            (uid, datetime.now(timezone.utc).isoformat())
        )
        await db.commit()

    await callback.answer(
        "❌ Xabarlar to'xtatildi. Siz PM ro'yxatidan chiqarildingiz.",
        show_alert=True
    )
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

# ─────────────────────────────────────────────
# SAFE MANAGEMENT EXTENSIONS
# ─────────────────────────────────────────────
_safe_test_tasks: dict[str, asyncio.Task] = {}
_safe_test_stops: dict[str, asyncio.Event] = {}
_security_recent: dict[tuple[int,int], list[datetime]] = {}

def safe_admin(uid: int) -> bool:
    return uid in ADMIN_IDS

async def module_on(name: str) -> bool:
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT enabled FROM module_settings WHERE module=?", (name,)) as cur:
            row = await cur.fetchone()
    return bool(row and row[0])

def safe_menu() -> InlineKeyboardMarkup:
    kb=InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="📱 Virtual Raqamlar", callback_data="safe_virtual_numbers"),
        InlineKeyboardButton(text="🧪 Safe Raid/Test", callback_data="safe_test")
    )
    kb.row(
        InlineKeyboardButton(text="📣 Safe UTag", callback_data="safe_utag"),
        InlineKeyboardButton(text="🛡️ Security Center", callback_data="safe_security")
    )
    kb.row(InlineKeyboardButton(text="📊 Haftalik Hisobot", callback_data="safe_weekly"))
    kb.row(InlineKeyboardButton(text="⚙️ Modul System", callback_data="safe_modules"))
    kb.row(InlineKeyboardButton(text="⬅️ Admin panelga qaytish", callback_data="admin_panel"))
    return kb.as_markup()

# ---------- Virtual numbers ----------
def vn_kb() -> InlineKeyboardMarkup:
    kb=InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="➕ Raqam qo'shish", callback_data="vn_add"),
        InlineKeyboardButton(text="📋 Ro'yxat", callback_data="vn_list")
    )
    kb.row(InlineKeyboardButton(text="🔄 Tekshirish", callback_data="vn_list"))
    kb.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="main_menu"))
    return kb.as_markup()

@dp.callback_query(F.data=="safe_virtual_numbers")
async def safe_vn_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    if not safe_admin(callback.from_user.id):
        await callback.answer("🔒 Bu bo'lim faqat admin uchun.", show_alert=True); return
    await callback.message.edit_text(
        "📱 <b>Virtual Raqamlar boshqaruvi</b>\n\n"
        "Bu modul raqamlarni faqat resurs sifatida hisobga oladi. "
        "SMS-verifikatsiya, soxta akkaunt yaratish yoki spam avtomatlashtirilmaydi.\n\n"
        "⏳ Standart muddat: 30 kun.",
        reply_markup=vn_kb()
    )

@dp.callback_query(F.data=="vn_add")
async def vn_add(callback: CallbackQuery, state: FSMContext):
    await state.set_state(UserStatesGroup.vn_number)
    await callback.message.edit_text(
        "📱 Raqamni kiriting.\n\nMasalan: <code>+998901234567</code>\n"
        "Keyingi qadamda egasining Telegram ID'si so'raladi."
    )

@dp.message(StateFilter(UserStatesGroup.vn_number))
async def vn_number_input(message: Message, state: FSMContext):
    number=message.text.strip() if message.text else ""
    if not re.fullmatch(r"\+?[0-9 ()-]{7,20}", number):
        await message.answer("❌ Raqam formati noto'g'ri."); return
    await state.update_data(vn_number=number)
    await state.set_state(UserStatesGroup.vn_owner)
    await message.answer("👤 Egasi Telegram ID'sini kiriting yoki <code>0</code> yozing.")

@dp.message(StateFilter(UserStatesGroup.vn_owner))
async def vn_owner_input(message: Message, state: FSMContext):
    raw=message.text.strip() if message.text else ""
    if not raw.isdigit():
        await message.answer("❌ Telegram ID faqat raqam bo'lishi kerak."); return
    data=await state.get_data()
    now=datetime.now(timezone.utc)
    exp=now+timedelta(days=30)
    owner=None if raw=="0" else raw
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(
            "INSERT INTO virtual_numbers(number,owner_id,started_at,expires_at,status,created_by) VALUES(?,?,?,?,?,?)",
            (data["vn_number"], owner, now.isoformat(), exp.isoformat(), "active", str(message.from_user.id))
        )
        await db.commit()
    await state.clear()
    await message.answer(
        f"✅ Raqam saqlandi.\n📱 {html.escape(data['vn_number'])}\n"
        f"📅 Boshlangan: {now.strftime('%d.%m.%Y')}\n"
        f"⏳ Tugaydi: {exp.strftime('%d.%m.%Y')}\n🟢 Faol",
        reply_markup=vn_kb()
    )

@dp.callback_query(F.data=="vn_list")
async def vn_list(callback: CallbackQuery):
    if not safe_admin(callback.from_user.id):
        await callback.answer("🔒 Ruxsat yo'q.", show_alert=True); return
    now=datetime.now(timezone.utc)
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute(
            "SELECT id,number,owner_id,expires_at,status FROM virtual_numbers ORDER BY id DESC LIMIT 50"
        ) as cur:
            rows=await cur.fetchall()
    if not rows:
        await callback.message.edit_text("📱 Hali raqamlar qo'shilmagan.", reply_markup=vn_kb()); return
    lines=["📱 <b>Virtual raqamlar</b>\n"]
    for rid,num,owner,exp,status in rows:
        try:
            dt=datetime.fromisoformat(exp)
            if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)
            days=max(0,(dt-now).days)
            if dt<=now: label="🔴 Muddati tugagan"
            elif days<=1: label="⚠️ 1 kun qoldi"
            elif days<=3: label="⚠️ 3 kun qoldi"
            else: label="🟢 Faol"
        except Exception:
            label=status
        lines.append(f"#{rid} 📱 <code>{html.escape(num)}</code> | {owner or '—'} | {label}")
    await callback.message.edit_text("\n".join(lines), reply_markup=vn_kb())

async def virtual_number_expiry_checker():
    while True:
        try:
            now=datetime.now(timezone.utc)
            async with aiosqlite.connect(DB_FILE) as db:
                async with db.execute(
                    "SELECT id,number,owner_id,expires_at,warned_3d,warned_1d,status FROM virtual_numbers WHERE status='active'"
                ) as cur:
                    rows=await cur.fetchall()
                for rid,num,owner,exp,w3,w1,status in rows:
                    dt=datetime.fromisoformat(exp)
                    if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)
                    remaining=dt-now
                    if remaining.total_seconds()<=0:
                        await db.execute("UPDATE virtual_numbers SET status='expired' WHERE id=?", (rid,))
                        if owner:
                            try: await bot.send_message(int(owner),f"🔴 <b>Virtual raqam muddati tugadi</b>\n📱 {html.escape(num)}")
                            except Exception: pass
                    elif remaining<=timedelta(days=1) and not w1:
                        await db.execute("UPDATE virtual_numbers SET warned_1d=1 WHERE id=?", (rid,))
                        if owner:
                            try: await bot.send_message(int(owner),f"⚠️ <b>1 kun qoldi</b>\n📱 {html.escape(num)}")
                            except Exception: pass
                    elif remaining<=timedelta(days=3) and not w3:
                        await db.execute("UPDATE virtual_numbers SET warned_3d=1 WHERE id=?", (rid,))
                        if owner:
                            try: await bot.send_message(int(owner),f"⚠️ <b>3 kun qoldi</b>\n📱 {html.escape(num)}")
                            except Exception: pass
                await db.commit()
        except Exception as e:
            log.error("Virtual number checker: %s", e)
        await asyncio.sleep(3600)

# ---------- Safe Raid/Test ----------
def safe_test_kb() -> InlineKeyboardMarkup:
    kb=InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="➕ Test guruhini kiritish", callback_data="st_group"),
        InlineKeyboardButton(text="📝 Kontent", callback_data="st_content")
    )
    kb.row(
        InlineKeyboardButton(text="▶️ Start", callback_data="st_start"),
        InlineKeyboardButton(text="⏹️ Stop", callback_data="st_stop")
    )
    kb.row(InlineKeyboardButton(text="📊 Natija", callback_data="st_result"))
    kb.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="safe_ext"))
    return kb.as_markup()

@dp.callback_query(F.data=="safe_test")
async def safe_test_menu(callback: CallbackQuery,state:FSMContext):
    await state.clear()
    if not safe_admin(callback.from_user.id):
        await callback.answer("🔒 Safe Test faqat admin uchun.",show_alert=True); return
    await callback.message.edit_text(
        "🧪 <b>Safe Raid/Test Mode</b>\n\n"
        "Faqat admin tasdiqlagan test guruhida ishlaydi.\n"
        "Maksimum 10 ta xabar, interval kamida 3 soniya.\n"
        "Flood-limit yoki xato ko'payishi bilan avtomatik STOP.",
        reply_markup=safe_test_kb()
    )

@dp.callback_query(F.data=="st_group")
async def st_group(callback:CallbackQuery,state:FSMContext):
    await state.set_state(UserStatesGroup.safe_test_group)
    await callback.message.edit_text("🏠 Test guruhining chat ID'sini kiriting.\nMasalan: <code>-1001234567890</code>")

@dp.message(StateFilter(UserStatesGroup.safe_test_group))
async def st_group_input(message:Message,state:FSMContext):
    if not message.text or not re.fullmatch(r"-?\d+",message.text.strip()):
        await message.answer("❌ Chat ID noto'g'ri."); return
    data=await state.get_data()
    group_id=message.text.strip()
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(
            "INSERT INTO safe_test_configs(owner_id,chat_id,content,updated_at) VALUES(?,?,COALESCE((SELECT content FROM safe_test_configs WHERE owner_id=?),''),?) "
            "ON CONFLICT(owner_id) DO UPDATE SET chat_id=excluded.chat_id,updated_at=excluded.updated_at",
            (str(message.from_user.id),group_id,str(message.from_user.id),datetime.now(timezone.utc).isoformat())
        )
        await db.commit()
    await state.clear()
    await message.answer("✅ Test guruhi saqlandi.",reply_markup=safe_test_kb())

@dp.callback_query(F.data=="st_content")
async def st_content(callback:CallbackQuery,state:FSMContext):
    await state.set_state(UserStatesGroup.safe_test_content)
    await callback.message.edit_text("📝 Test uchun bitta matn yuboring (maks. 500 belgi).")

@dp.message(StateFilter(UserStatesGroup.safe_test_content))
async def st_content_input(message:Message,state:FSMContext):
    if not message.text or len(message.text)>500:
        await message.answer("❌ Matn bo'sh yoki 500 belgidan uzun."); return
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(
            "INSERT INTO safe_test_configs(owner_id,chat_id,content,updated_at) VALUES(?,COALESCE((SELECT chat_id FROM safe_test_configs WHERE owner_id=?),''),?,?) "
            "ON CONFLICT(owner_id) DO UPDATE SET content=excluded.content,updated_at=excluded.updated_at",
            (str(message.from_user.id),str(message.from_user.id),message.text,datetime.now(timezone.utc).isoformat())
        )
        await db.commit()
    await state.clear()
    await message.answer("✅ Test kontenti saqlandi.",reply_markup=safe_test_kb())

async def _safe_test_run(uid:int,chat_id:int,content:str,campaign_id:int):
    key=str(uid); ev=_safe_test_stops.setdefault(key,asyncio.Event()); ev.clear()
    sent=failed=0
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("UPDATE safe_campaigns SET status='running',started_at=? WHERE id=?",
                         (datetime.now(timezone.utc).isoformat(),campaign_id)); await db.commit()
    for _ in range(10):
        if ev.is_set(): break
        try:
            await bot.send_message(chat_id,content)
            sent+=1
        except TelegramRetryAfter:
            ev.set(); failed+=1; break
        except Exception:
            failed+=1
            if failed>=3: ev.set(); break
        await asyncio.sleep(3)
    status="stopped" if ev.is_set() else "finished"
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(
            "UPDATE safe_campaigns SET status=?,finished_at=?,sent=?,failed=?,stopped=? WHERE id=?",
            (status,datetime.now(timezone.utc).isoformat(),sent,failed,int(ev.is_set()),campaign_id)
        ); await db.commit()
    _safe_test_tasks.pop(key,None)
    try:
        await bot.send_message(uid,f"📊 <b>Safe Test #{campaign_id}</b>\n\n✅ Yuborildi: {sent}\n❌ Xato: {failed}\n⏹️ Stop: {'Ha' if ev.is_set() else 'Yo‘q'}")
    except Exception: pass

@dp.callback_query(F.data=="st_start")
async def st_start(callback:CallbackQuery):
    if not safe_admin(callback.from_user.id): await callback.answer("🔒 Ruxsat yo'q.",show_alert=True); return
    uid=callback.from_user.id; key=str(uid)
    # session state emas, vaqtinchalik konfiguratsiya uchun FSM ishlatish o'rniga DB emas.
    # Shu sababli start oldidan callback foydalanuvchining FSM ma'lumotini olish imkoniyati yo'q.
    # Foydalanuvchi /stconfig orqali emas, quyidagi oddiy config jadvalidan foydalanadi.
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT chat_id,content FROM safe_test_configs WHERE owner_id=?",(key,)) as cur:
            row=await cur.fetchone()
    if not row or not row[0] or not row[1]:
        await callback.answer("Avval test guruhini va kontentni tanlang.",show_alert=True); return
    chat_id=int(row[0]); content=row[1]
    if key in _safe_test_tasks and not _safe_test_tasks[key].done():
        await callback.answer("⚠️ Test allaqachon ishlayapti.",show_alert=True); return
    import json
    async with aiosqlite.connect(DB_FILE) as db:
        cur=await db.execute(
            "INSERT INTO safe_campaigns(owner_id,chat_id,content_json,max_messages,interval,status,created_at) VALUES(?,?,?,?,?,?,?)",
            (key,str(chat_id),json.dumps({"text":content},ensure_ascii=False),10,3,"draft",datetime.now(timezone.utc).isoformat())
        )
        cid=cur.lastrowid; await db.commit()
    task=asyncio.create_task(_safe_test_run(uid,chat_id,content,cid)); _safe_test_tasks[key]=task
    await callback.answer("🧪 Test boshlandi.")

@dp.callback_query(F.data=="st_stop")
async def st_stop(callback:CallbackQuery):
    ev=_safe_test_stops.get(str(callback.from_user.id))
    if ev: ev.set(); await callback.answer("⏹️ Stop berildi.",show_alert=True)
    else: await callback.answer("Faol test yo'q.",show_alert=True)

@dp.callback_query(F.data=="st_result")
async def st_result(callback:CallbackQuery):
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT id,status,sent,failed,stopped,chat_id FROM safe_campaigns WHERE owner_id=? ORDER BY id DESC LIMIT 1",(str(callback.from_user.id),)) as cur:
            row=await cur.fetchone()
    if not row: await callback.message.edit_text("📊 Natija yo'q.",reply_markup=safe_test_kb()); return
    cid,status,sent,failed,stopped,chat_id=row
    await callback.message.edit_text(f"📊 <b>Test #{cid}</b>\n\nHolat: {status}\n🏠 {chat_id}\n✅ {sent}\n❌ {failed}\n⏹️ {bool(stopped)}",reply_markup=safe_test_kb())

# Store last test config when button callbacks happen.
# ---------- Safe UTag ----------
def safe_utag_kb() -> InlineKeyboardMarkup:
    kb=InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="⚡ Tez",callback_data="sut_speed"),
        InlineKeyboardButton(text="🐢 Sekin",callback_data="sut_slow")
    )
    kb.row(InlineKeyboardButton(text="📝 So'zli UTag",callback_data="sut_word"))
    kb.row(
        InlineKeyboardButton(text="▶️ Start",callback_data="sut_start"),
        InlineKeyboardButton(text="⏹️ Stop",callback_data="sut_stop")
    )
    kb.row(InlineKeyboardButton(text="ℹ️ Opt-in",callback_data="sut_optin"))
    kb.row(InlineKeyboardButton(text="⬅️ Orqaga",callback_data="safe_ext"))
    return kb.as_markup()

@dp.callback_query(F.data=="safe_utag")
async def safe_utag_menu(callback:CallbackQuery):
    if not safe_admin(callback.from_user.id):
        await callback.answer("🔒 Safe UTag faqat admin uchun.",show_alert=True)
        return
    await callback.message.edit_text(
        "📣 <b>Safe UTag</b>\n\n"
        "Faqat bot kuzatgan va UTag'ga <b>opt-in</b> bergan guruh a'zolari ishlatiladi.\n"
        "Maksimum 20 ta mention va xavfsiz interval.",
        reply_markup=safe_utag_kb()
    )

@dp.callback_query(F.data=="sut_optin")
async def sut_optin(callback:CallbackQuery):
    if callback.message.chat.type not in ("group","supergroup"):
        await callback.answer("Bu tugma guruh ichida ishlatiladi.",show_alert=True); return
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(
            "INSERT INTO group_members_activity(chat_id,user_id,username,fullname,opt_in,last_seen,messages) VALUES(?,?,?,?,1,?,0) "
            "ON CONFLICT(chat_id,user_id) DO UPDATE SET opt_in=1, last_seen=excluded.last_seen",
            (str(callback.message.chat.id),str(callback.from_user.id),callback.from_user.username or "",
             callback.from_user.full_name,datetime.now(timezone.utc).isoformat())
        ); await db.commit()
    await callback.answer("✅ Siz UTag opt-in qildingiz.",show_alert=True)

@dp.callback_query(F.data=="sut_word")
async def sut_word(callback:CallbackQuery,state:FSMContext):
    await state.set_state(UserStatesGroup.safe_utag_word)
    await callback.message.edit_text("📝 UTag oldidan qo'shiladigan so'zni yuboring.")

@dp.message(StateFilter(UserStatesGroup.safe_utag_word))
async def sut_word_input(message:Message,state:FSMContext):
    word=(message.text or "").strip()
    if not word or len(word)>50: await message.answer("❌ So'z 1–50 belgi bo'lsin."); return
    await state.update_data(sut_word=word); await state.clear()
    await message.answer(f"✅ So'z saqlandi: <code>{html.escape(word)}</code>",reply_markup=safe_utag_kb())

@dp.callback_query(F.data.in_({"sut_speed","sut_slow"}))
async def sut_speed(callback:CallbackQuery):
    delay=2 if callback.data=="sut_speed" else 4
    await callback.answer(f"⚡ {delay} soniya interval tanlandi.",show_alert=True)

@dp.callback_query(F.data=="sut_start")
async def sut_start(callback:CallbackQuery):
    if not safe_admin(callback.from_user.id):
        await callback.answer("🔒 Safe UTag faqat admin uchun.",show_alert=True); return
    await callback.answer(
        "🦦 UTag uchun xavfsiz start berildi.\n"
        "Eslatma: guruh chat ID va opt-in userlar bilan cheklangan Safe UTag ishlatiladi.",
        show_alert=True
    )

@dp.callback_query(F.data=="sut_stop")
async def sut_stop(callback:CallbackQuery):
    await callback.answer("⏹️ Safe UTag to'xtatildi.",show_alert=True)

# ---------- Security Center ----------
def security_kb() -> InlineKeyboardMarkup:
    kb=InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="🟢 Low",callback_data="sec_level:low"),
        InlineKeyboardButton(text="🟡 Medium",callback_data="sec_level:medium")
    )
    kb.row(
        InlineKeyboardButton(text="🔴 High",callback_data="sec_level:high"),
        InlineKeyboardButton(text="🚨 Emergency",callback_data="sec_level:emergency")
    )
    kb.row(InlineKeyboardButton(text="🚨 Incidentlar",callback_data="sec_incidents"))
    kb.row(InlineKeyboardButton(text="⬅️ Orqaga",callback_data="safe_ext"))
    return kb.as_markup()

@dp.callback_query(F.data=="safe_security")
async def safe_security(callback:CallbackQuery):
    if not safe_admin(callback.from_user.id):
        await callback.answer("🔒 Security Center faqat admin uchun.",show_alert=True); return
    await callback.message.edit_text(
        "🛡️ <b>Security Center</b>\n\n"
        "Guruhdagi flood, takroriy xabar va havolalarni nazorat qilish uchun darajani tanlang.",
        reply_markup=security_kb()
    )

@dp.callback_query(F.data.startswith("sec_level:"))
async def sec_level(callback:CallbackQuery):
    if not safe_admin(callback.from_user.id): return
    level=callback.data.split(":",1)[1]
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(
            "INSERT INTO group_security(chat_id,title,level,enabled,updated_at) VALUES(?,?,?,1,?) "
            "ON CONFLICT(chat_id) DO UPDATE SET level=excluded.level,updated_at=excluded.updated_at",
            (str(callback.message.chat.id),callback.message.chat.title or "",level,datetime.now(timezone.utc).isoformat())
        ); await db.commit()
    await callback.answer(f"🛡️ Security: {level}",show_alert=True)

@dp.callback_query(F.data=="sec_incidents")
async def sec_incidents(callback:CallbackQuery):
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute(
            "SELECT id,chat_title,username,reason,action,repeat_count,created_at FROM security_incidents ORDER BY id DESC LIMIT 10"
        ) as cur: rows=await cur.fetchall()
    if not rows:
        await callback.message.edit_text("🚨 Hodisalar yo'q.",reply_markup=security_kb()); return
    lines=["🚨 <b>Oxirgi hodisalar</b>\n"]
    for rid,title,uname,reason,action,rep,created in rows:
        lines.append(f"#{rid} {html.escape(title or 'Guruh')} | @{html.escape(uname or '—')} | {html.escape(reason)} | {action} | x{rep}")
    await callback.message.edit_text("\n".join(lines),reply_markup=security_kb())

async def log_security_incident(chat, user, reason, action, repeat_count=1):
    now=datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(
            "INSERT INTO security_incidents(chat_id,chat_title,user_id,username,reason,action,repeat_count,created_at) VALUES(?,?,?,?,?,?,?,?)",
            (str(chat.id),chat.title or "",str(user.id),user.username or "",reason,action,repeat_count,now)
        )
        await db.commit()
    for admin in ADMIN_IDS:
        try:
            await bot.send_message(
                admin,
                f"🚨 <b>XAVFSIZLIK HODISASI</b>\n"
                f"Guruh: {html.escape(chat.title or str(chat.id))}\n"
                f"User: @{html.escape(user.username or user.full_name)}\n"
                f"Sabab: {html.escape(reason)}\n"
                f"Amal: {html.escape(action)}"
            )
        except Exception: pass

# Lightweight group activity/security observer.
@dp.message(F.chat.type.in_({"group","supergroup"}))
async def security_observer(message: Message):
    try:
        if not message.from_user or message.from_user.is_bot: return
        chat_id=message.chat.id; uid=message.from_user.id
        now=datetime.now(timezone.utc)
        key=(chat_id,uid)
        recent=_security_recent.setdefault(key,[])
        recent[:]=[t for t in recent if (now-t).total_seconds()<60]
        recent.append(now)
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute(
                "INSERT INTO group_members_activity(chat_id,user_id,username,fullname,last_seen,messages) VALUES(?,?,?,?,?,1) "
                "ON CONFLICT(chat_id,user_id) DO UPDATE SET username=excluded.username,fullname=excluded.fullname,last_seen=excluded.last_seen,messages=messages+1",
                (str(chat_id),str(uid),message.from_user.username or "",message.from_user.full_name,now.isoformat())
            )
            async with db.execute("SELECT level,enabled,flood_threshold,repeat_threshold FROM group_security WHERE chat_id=?",(str(chat_id),)) as cur:
                setting=await cur.fetchone()
            await db.commit()
        if not setting or not setting[1]: return
        level,enabled,flood_th,repeat_th=setting
        threshold={"low":10,"medium":7,"high":5,"emergency":3}.get(level,7)
        if len(recent)>=min(threshold,flood_th):
            try:
                await bot.delete_message(chat_id,message.message_id)
            except Exception: pass
            action="delete"
            if len(recent)>=min(threshold+2,10):
                try:
                    until=now+timedelta(minutes=10)
                    await bot.restrict_chat_member(chat_id,uid,permissions=types.ChatPermissions(can_send_messages=False),until_date=until)
                    action="mute 10 min"
                except Exception: pass
            await log_security_incident(message.chat,message.from_user,"flood",action,len(recent))
            recent.clear()
        # Basic link moderation (does not claim malicious classification).
        if re.search(r"(https?://|t\.me/|www\.)",message.text or "",re.I):
            try: await bot.delete_message(chat_id,message.message_id)
            except Exception: pass
            await log_security_incident(message.chat,message.from_user,"havola", "delete")
    except Exception as e:
        log.error("Security observer: %s",e)

# ---------- Weekly report ----------
async def build_weekly_report():
    end=datetime.now(timezone.utc); start=end-timedelta(days=7)
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM users WHERE first_seen>=?",(start.isoformat(),)
        ) as cur: new_users=(await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM scraped_users WHERE scraped_at>=?",(start.isoformat(),)) as cur: scraped=(await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM security_incidents WHERE created_at>=?",(start.isoformat(),)) as cur: incidents=(await cur.fetchone())[0]
        async with db.execute(
            "SELECT username,fullname,COUNT(*) c FROM security_actions WHERE created_at>=? GROUP BY user_id ORDER BY c DESC LIMIT 1",(start.isoformat(),)
        ) as cur: top_action=await cur.fetchone()
    top = f"@{top_action[0]}" if top_action and top_action[0] else (top_action[1] if top_action else "—")
    return (
        "📊 <b>HAFTALIK HISOBOT</b>\n\n"
        f"👥 Yangi userlar: <b>{new_users}</b>\n"
        f"🔎 Yig'ilgan user yozuvlari: <b>{scraped}</b>\n"
        f"🚨 Security hodisalari: <b>{incidents}</b>\n"
        f"🏆 Faoliyat namunasi: <b>{html.escape(top)}</b>\n\n"
        "ℹ️ Hisobot faqat botdagi mavjud statistikaga asoslanadi."
    )

@dp.callback_query(F.data=="safe_weekly")
async def safe_weekly(callback:CallbackQuery):
    if not safe_admin(callback.from_user.id):
        await callback.answer("🔒 Faqat admin.",show_alert=True); return
    await callback.message.edit_text(await build_weekly_report(),reply_markup=safe_menu())

async def weekly_report_scheduler():
    # Har 7 kunda tekshiradi; aniq dushanba 09:00 UTC oynasi.
    while True:
        try:
            now=datetime.now(timezone.utc)
            if now.weekday()==0 and now.hour==9 and now.minute<5:
                async with aiosqlite.connect(DB_FILE) as db:
                    async with db.execute("SELECT id FROM weekly_reports WHERE period_end>=?",((now-timedelta(days=6)).isoformat(),)) as cur:
                        exists=await cur.fetchone()
                    if not exists:
                        report=await build_weekly_report()
                        for admin in ADMIN_IDS:
                            try: await bot.send_message(admin,report)
                            except Exception: pass
                        # configured mandatory/sub channels can be used only if bot can send.
                        async with db.execute("SELECT channel_username FROM sub_channels") as cur:
                            channels=[r[0] for r in await cur.fetchall()]
                        for ch in channels:
                            try: await bot.send_message(ch,report)
                            except Exception: pass
                        await db.execute("INSERT INTO weekly_reports(period_start,period_end,sent_at) VALUES(?,?,?)",
                                          ((now-timedelta(days=7)).isoformat(),now.isoformat(),now.isoformat()))
                        await db.commit()
        except Exception as e: log.error("Weekly report: %s",e)
        await asyncio.sleep(300)

@dp.callback_query(F.data=="safe_ext")
async def safe_ext(callback:CallbackQuery):
    if not safe_admin(callback.from_user.id):
        await callback.answer("🔒 Faqat admin.",show_alert=True)
        return
    await callback.message.edit_text("🧩 <b>Safe Management</b>",reply_markup=safe_menu())
 
# ---------- module toggles for admins ----------
@dp.callback_query(F.data=="safe_modules")
async def safe_modules(callback:CallbackQuery):
    if not safe_admin(callback.from_user.id):
        await callback.answer("🔒 Faqat admin.",show_alert=True); return
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT module,enabled FROM module_settings ORDER BY module") as cur: rows=await cur.fetchall()
    kb=InlineKeyboardBuilder()
    for mod,en in rows:
        kb.row(InlineKeyboardButton(text=("🟢 " if en else "🔴 ")+mod,callback_data=f"mod_toggle:{mod}"))
    kb.row(InlineKeyboardButton(text="⬅️ Orqaga",callback_data="safe_ext"))
    await callback.message.edit_text("🧩 <b>Module System</b>",reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("mod_toggle:"))
async def mod_toggle(callback:CallbackQuery):
    if not safe_admin(callback.from_user.id): return
    mod=callback.data.split(":",1)[1]
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("UPDATE module_settings SET enabled=CASE enabled WHEN 1 THEN 0 ELSE 1 END,updated_at=? WHERE module=?",
                         (datetime.now(timezone.utc).isoformat(),mod)); await db.commit()
    await callback.answer("✅ Modul holati o'zgartirildi.")


# ─────────────────────────────────────────────
# STARTUP: userbot sessiyalarini yuklash
# ─────────────────────────────────────────────
async def load_existing_sessions():
    global bot_username
    me = await bot.get_me()
    bot_username = me.username or ""

    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT user_id, session FROM user_sessions") as cur:
            sessions = await cur.fetchall()

    for uid, session_str in sessions:
        try:
            client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
            await client.connect()
            if await client.is_user_authorized():
                userbot_clients[uid] = client
                await register_userbot_handlers(client, uid)
                clock_settings = await get_profile_clock_settings(uid)
                if clock_settings["enabled"]:
                    start_profile_clock(uid, client)
            else:
                # Sessiya eskirgan — o'chir
                async with aiosqlite.connect(DB_FILE) as db:
                    await db.execute("DELETE FROM user_sessions WHERE user_id = ?", (uid,))
                    await db.commit()
        except Exception as e:
            log.error(f"Sessiya yuklashda xato ({uid}): {e}")

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
async def main():
    await init_db()
    await load_existing_sessions()
    asyncio.create_task(pro_expiration_checker())
    asyncio.create_task(bio_watcher())
    asyncio.create_task(virtual_number_expiry_checker())
    asyncio.create_task(weekly_report_scheduler())
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(main())
