from sqlalchemy import func, select, update

from kino_bot.database.engine import SessionLocal
from kino_bot.database.models import ForceSubChannel


async def add_channel(
    chat_id: str,
    title: str,
    username: str | None,
    invite_link: str | None,
    added_by: int,
) -> ForceSubChannel:
    async with SessionLocal() as session:
        channel = await session.scalar(
            select(ForceSubChannel).where(ForceSubChannel.chat_id == str(chat_id))
        )
        if channel:
            channel.title = title
            channel.username = username
            channel.invite_link = invite_link
            channel.is_active = True
        else:
            channel = ForceSubChannel(
                chat_id=str(chat_id),
                title=title,
                username=username,
                invite_link=invite_link,
                added_by=added_by,
            )
            session.add(channel)
        await session.commit()
        await session.refresh(channel)
        return channel


async def active_channels() -> list[ForceSubChannel]:
    async with SessionLocal() as session:
        result = await session.scalars(
            select(ForceSubChannel).where(ForceSubChannel.is_active.is_(True))
        )
        return list(result)


async def all_channels() -> list[ForceSubChannel]:
    async with SessionLocal() as session:
        result = await session.scalars(
            select(ForceSubChannel).order_by(ForceSubChannel.added_at.desc())
        )
        return list(result)


async def deactivate_channel(channel_id: int) -> bool:
    async with SessionLocal() as session:
        result = await session.execute(
            update(ForceSubChannel)
            .where(ForceSubChannel.id == channel_id)
            .values(is_active=False)
        )
        await session.commit()
        return result.rowcount > 0


async def count_active_channels() -> int:
    async with SessionLocal() as session:
        return (
            await session.scalar(
                select(func.count(ForceSubChannel.id)).where(
                    ForceSubChannel.is_active.is_(True)
                )
            )
            or 0
        )
