from kino_bot.database.crud.movies import generate_next_code


async def make_unique_movie_code() -> str:
    return await generate_next_code()
