from datetime import datetime, timedelta

from sqlalchemy import func, select, update

from kino_bot.database.engine import SessionLocal
from kino_bot.database.models import User


async def upsert_user(telegram_id: int, full_name: str, username: str | None) -> User:
    async with SessionLocal() as session:
        user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
        if user:
            user.full_name = full_name
            user.username = username
        else:
            user = User(telegram_id=telegram_id, full_name=full_name, username=username)
            session.add(user)
        await session.commit()
        return user


async def get_all_users() -> list[User]:
    async with SessionLocal() as session:
        result = await session.scalars(select(User).where(User.is_blocked.is_(False)))
        return list(result)


async def get_user(telegram_id: int) -> User | None:
    async with SessionLocal() as session:
        return await session.scalar(select(User).where(User.telegram_id == telegram_id))


async def count_users() -> int:
    async with SessionLocal() as session:
        return await session.scalar(select(func.count(User.id))) or 0


async def count_today_users() -> int:
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    async with SessionLocal() as session:
        return (
            await session.scalar(select(func.count(User.id)).where(User.joined_at >= today))
            or 0
        )


async def latest_users(limit: int = 10) -> list[User]:
    async with SessionLocal() as session:
        result = await session.scalars(
            select(User).order_by(User.joined_at.desc()).limit(limit)
        )
        return list(result)


async def set_user_blocked(telegram_id: int, blocked: bool) -> bool:
    async with SessionLocal() as session:
        result = await session.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(is_blocked=blocked)
        )
        await session.commit()
        return result.rowcount > 0
