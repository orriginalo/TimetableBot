from datetime import datetime
from pydantic import BaseModel


class UserSchema(BaseModel):
    uid: int
    tg_id: int
    role: int
    username: str | None
    firstname: str | None
    lastname: str | None
    settings: dict
    created_at: datetime
    updated_at: datetime
    group_id: int | None
    group_name: str | None
    recent_groups: list[str] | None


class GroupSchema(BaseModel):
    uid: int
    name: str
