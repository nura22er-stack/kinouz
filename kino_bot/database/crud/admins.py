from sqlalchemy import delete, select

from kino_bot.database.engine import SessionLocal
from kino_bot.database.models import Admin


async def ensure_super_admins(admin_ids: list[int]) -> None:
    async with SessionLocal() as session:
        for admin_id in admin_ids:
            admin = await session.scalar(select(Admin).where(Admin.telegram_id == admin_id))
            if admin:
                admin.is_super_admin = True
            else:
                session.add(Admin(telegram_id=admin_id, is_super_admin=True))
        await session.commit()


async def ensure_super_admin(telegram_id: int) -> None:
    async with SessionLocal() as session:
        admin = await session.scalar(select(Admin).where(Admin.telegram_id == telegram_id))
        if admin:
            admin.is_super_admin = True
        else:
            session.add(Admin(telegram_id=telegram_id, is_super_admin=True))
        await session.commit()


async def is_admin(telegram_id: int) -> bool:
    async with SessionLocal() as session:
        admin = await session.scalar(select(Admin).where(Admin.telegram_id == telegram_id))
        return admin is not None


async def is_super_admin(telegram_id: int) -> bool:
    async with SessionLocal() as session:
        admin = await session.scalar(select(Admin).where(Admin.telegram_id == telegram_id))
        return bool(admin and admin.is_super_admin)


async def add_admin(telegram_id: int, added_by: int) -> None:
    async with SessionLocal() as session:
        admin = await session.scalar(select(Admin).where(Admin.telegram_id == telegram_id))
        if not admin:
            session.add(Admin(telegram_id=telegram_id, added_by=added_by))
        await session.commit()


async def remove_admin(telegram_id: int) -> bool:
    async with SessionLocal() as session:
        admin = await session.scalar(select(Admin).where(Admin.telegram_id == telegram_id))
        if not admin or admin.is_super_admin:
            return False
        await session.delete(admin)
        await session.commit()
        return True
