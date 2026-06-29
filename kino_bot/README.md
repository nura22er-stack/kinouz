# Telegram Kino Bot

Aiogram 3, SQLAlchemy async va SQLite asosida yozilgan kino ulashish boti.

## O'rnatish

```bash
cd kino_bot
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

`.env` faylini to'ldiring:

```env
BOT_TOKEN=telegram_bot_token
ADMIN_IDS=123456789
DATABASE_URL=sqlite+aiosqlite:///kino_bot.db
MAIN_CHANNEL_ID=-1001234567890
```

Bot kanalga kino post qilishi va majburiy obunani tekshirishi uchun u kanallarda admin bo'lishi kerak.

## Ishga tushirish

```bash
python bot.py
```

Jadvallar birinchi ishga tushirishda avtomatik yaratiladi. Alembic konfiguratsiyasi ham qo'shilgan; keyingi o'zgarishlar uchun migratsiya chiqarish mumkin.

## Render

Render'da Background Worker yarating:

- Build command: `pip install -r requirements.txt`
- Start command: `python bot.py`

Environment variables:

```env
BOT_TOKEN=telegram_bot_token
ADMIN_IDS=123456789
ADMIN_USERNAMES=MYesemin,ismoiljonov_2209
DATABASE_URL=sqlite+aiosqlite:///kino_bot.db
MAIN_CHANNEL_ID=-1001234567890
LOG_FILE=bot.log
```

`BOT_TOKEN` va boshqa maxfiy qiymatlarni GitHub'ga push qilmang, Render dashboard orqali kiriting.
