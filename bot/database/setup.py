from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os
from dotenv import load_dotenv

load_dotenv(override=True)

sqlalchemy_url = os.getenv("SQLALCHEMY_URL")
sqlalchemy_url_sync = os.getenv("SQLALCHEMY_URL_SYNC")

async_engine = create_async_engine(
    url=sqlalchemy_url,
    # echo=True,
    pool_size=5,
)

sync_engine = create_engine(
    url=sqlalchemy_url_sync,
    # echo=True,
    pool_size=5,
)

session = async_sessionmaker(async_engine)


class Base(DeclarativeBase):
    pass
