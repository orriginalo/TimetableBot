from bot.database.setup import session
from sqlalchemy import select, update
from bot.database.models import Settings


async def get_setting(key: str):
    async with session() as s:
        stmt = select(Settings).where(Settings.key == key)
        result = await s.execute(stmt)
        setting = result.scalar_one_or_none()
        return setting.value if setting else None


async def set_setting(key: str, value: str):
    async with session() as s:
        stmt = select(Settings).where(Settings.key == key)
        result = await s.execute(stmt)
        setting = result.scalar_one_or_none()

        if setting:
            await s.execute(
                update(Settings).where(Settings.key == key).values(value=value)
            )
        else:
            new_setting = Settings(key=key, value=value)
            s.add(new_setting)

        await s.commit()
