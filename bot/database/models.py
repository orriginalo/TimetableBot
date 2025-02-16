from datetime import datetime
from typing import Annotated
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, text

from sqlalchemy.dialects.postgresql import JSONB, BIGINT

from bot.database.setup import Base

import variables as var

intpk = Annotated[int, mapped_column(primary_key=True, autoincrement=True)]
created_at = Annotated[datetime, mapped_column(server_default=text("TIMEZONE('UTC-4', CURRENT_TIMESTAMP)"))]
updated_at = Annotated[datetime, mapped_column(server_default=text("TIMEZONE('UTC-4', CURRENT_TIMESTAMP)"), onupdate=text("TIMEZONE('UTC-4', CURRENT_TIMESTAMP)"))]

class User(Base):
  __tablename__ = "users"
  uid: Mapped[intpk]
  tg_id: Mapped[int] = mapped_column(BIGINT, unique=True)
  role: Mapped[int]
  username: Mapped[str | None]
  firstname: Mapped[str | None]
  lastname: Mapped[str | None]
  settings: Mapped[dict] = mapped_column(JSONB, default=var.default_user_settings)
  created_at: Mapped[created_at]
  updated_at: Mapped[updated_at]
  group_id: Mapped[int | None]
  group_name: Mapped[str | None]
  recent_groups: Mapped[list[str]]

class Groups(Base):
  __tablename__ = "groups"
  uid: Mapped[intpk]
  name: Mapped[str]

class Settings(Base):
  __tablename__ = "settings"
  uid: Mapped[intpk]
  key: Mapped[str]
  value: Mapped[str]