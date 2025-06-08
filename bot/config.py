import os
from pydantic import BaseModel


class Config(BaseModel):
    BOT_TOKEN: str = os.getenv('BOT_TOKEN')

    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')

    API_HOST: str = os.getenv('API_HOST')
    API_PORT: str = os.getenv('API_PORT')

    POSTGRES_HOST: str = os.getenv('POSTGRES_HOST')
    POSTGRES_PORT: str = os.getenv('POSTGRES_PORT')
    POSTGRES_USER: str = os.getenv('POSTGRES_USER')
    POSTGRES_DB: str = os.getenv('POSTGRES_DB')
    POSTGRES_PASSWORD: str = os.getenv('POSTGRES_PASSWORD')

    BLACKLISTED_USERS: list[int] = [int(tg_id) for tg_id in os.getenv('BLACKLISTED_IDS', '').split(',')]
    OWNER_ID: int = int(os.getenv('OWNER_ID'))

    @property
    def API_URL(self) -> str:
        return f'http://{self.API_HOST}:{self.API_PORT}'

    @property
    def SQLALCHEMY_URL(self) -> str:
        return f'postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}'

    @property
    def SQLALCHEMY_URL_SYNC(self) -> str:
        return f'postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}'

    DEFAULT_USER_SETTINGS: dict = {
        "send_timetable_new_week": True,
        "send_timetable_updated": False,
        "send_changes_updated": True,
        "send_changes_when_isnt_group": True,
        "only_page_with_group_in_changes": False,
    }



settings = Config()
