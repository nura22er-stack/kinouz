from sqlalchemy import delete, func, select, update

from kino_bot.database.engine import SessionLocal
from kino_bot.database.models import Movie


async def generate_next_code(start: int = 1000) -> str:
    async with SessionLocal() as session:
        codes = await session.scalars(select(Movie.code))
        numeric_codes = [int(code) for code in codes if str(code).isdigit()]
        return str(max(numeric_codes, default=start - 1) + 1)


async def create_movie(
    code: str,
    title: str,
    file_id: str,
    caption: str | None,
    added_by: int,
    poster_file_id: str | None = None,
    channel_message_id: int | None = None,
) -> Movie:
    async with SessionLocal() as session:
        movie = Movie(
            code=code,
            title=title,
            poster_file_id=poster_file_id,
            file_id=file_id,
            caption=caption,
            added_by=added_by,
            channel_message_id=channel_message_id,
        )
        session.add(movie)
        await session.commit()
        await session.refresh(movie)
        return movie


async def get_movie_by_code(code: str) -> Movie | None:
    async with SessionLocal() as session:
        return await session.scalar(select(Movie).where(Movie.code == code))


async def increment_views(code: str) -> None:
    async with SessionLocal() as session:
        await session.execute(
            update(Movie)
            .where(Movie.code == code)
            .values(views_count=Movie.views_count + 1)
        )
        await session.commit()


async def delete_movie_by_code(code: str) -> Movie | None:
    async with SessionLocal() as session:
        movie = await session.scalar(select(Movie).where(Movie.code == code))
        if not movie:
            return None
        await session.delete(movie)
        await session.commit()
        return movie


async def list_movies(page: int = 1, per_page: int = 10) -> tuple[list[Movie], int]:
    offset = (page - 1) * per_page
    async with SessionLocal() as session:
        total = await session.scalar(select(func.count(Movie.id))) or 0
        result = await session.scalars(
            select(Movie).order_by(Movie.created_at.desc()).offset(offset).limit(per_page)
        )
        return list(result), total


async def count_movies() -> int:
    async with SessionLocal() as session:
        return await session.scalar(select(func.count(Movie.id))) or 0


async def top_movies(limit: int = 5) -> list[Movie]:
    async with SessionLocal() as session:
        result = await session.scalars(
            select(Movie).order_by(Movie.views_count.desc()).limit(limit)
        )
        return list(result)


async def update_channel_message_id(code: str, message_id: int) -> None:
    async with SessionLocal() as session:
        await session.execute(
            update(Movie)
            .where(Movie.code == code)
            .values(channel_message_id=message_id)
        )
        await session.commit()
