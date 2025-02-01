from datetime import datetime
from typing import Annotated
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, text

from sqlalchemy.dialects.mysql import JSON

from bot.database.setup import Base

import globals as G

intpk = Annotated[int, mapped_column(primary_key=True)]
created_at = Annotated[str, mapped_column(server_default=text("TIMEZONE('UTC-4', CURRENT_TIMESTAMP)"))]
updated_at = Annotated[str, mapped_column(server_default=text("TIMEZONE('UTC-4', CURRENT_TIMESTAMP)"), onupdate=text("TIMEZONE('UTC-4', CURRENT_TIMESTAMP)"))]

class User(Base):
  __tablename__ = "users"
  uid: Mapped[intpk]
  tg_id: Mapped[int] = mapped_column(unique=True)
  role: Mapped[int]
  username: Mapped[str | None]
  firstname: Mapped[str | None]
  lastname: Mapped[str | None]
  settings: Mapped[dict] = mapped_column(JSON, default=G.default_user_settings)
  created_at: Mapped[created_at]
  updated_at: Mapped[updated_at]
  group_id: Mapped[int | None]
  group_name: Mapped[str | None]
  is_leader: Mapped[bool]

class Groups(Base):
  __tablename__ = "groups"
  uid: Mapped[intpk]
  name: Mapped[str]
  course: Mapped[int | None]