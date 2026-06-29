from sqlalchemy import select

from kino_bot.database.engine import SessionLocal
from kino_bot.database.models import BotSetting


async def get_setting(key: str, default: str | None = None) -> str | None:
    async with SessionLocal() as session:
        setting = await session.scalar(select(BotSetting).where(BotSetting.key == key))
        return setting.value if setting else default


async def set_setting(key: str, value: str | None) -> None:
    async with SessionLocal() as session:
        setting = await session.scalar(select(BotSetting).where(BotSetting.key == key))
        if setting:
            setting.value = value
        else:
            session.add(BotSetting(key=key, value=value))
        await session.commit()
