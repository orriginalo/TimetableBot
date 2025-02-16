from bot.database.setup import session
from bot.database.models import Groups
from sqlalchemy import and_, select
from utils.log import logger
from bot.database.schemas import GroupSchema

async def add_group(name: str):
  try:
    async with session() as s:
      group = Groups(
        name=name.lower(),
      )
      s.add(group)
      await s.commit()
      logger.debug(f"Group {name} successfully added!")
      return GroupSchema.model_validate(group, from_attributes=True) if group else None
  except Exception as e:
    logger.exception(f"Error adding group: {e}")
    return None

async def delete_all_groups():
  try:
    async with session() as s:
      stmt = select(Groups)
      result = await s.execute(stmt)
      groups = result.scalars().all()
      for group in groups:
        s.delete(group)
      await s.commit()
      logger.debug(f"All groups successfully deleted!")
  except Exception as e:
    logger.exception(f"Error deleting all groups: {e}")
    return None

async def update_group(group_id: int, **kwargs):
  try:
    async with session() as s:
      stmt = select(Groups).where(Groups.uid == group_id)
      result = await s.execute(stmt)
      group = result.scalar_one_or_none()
      if group:
        for key, value in kwargs.items():
          setattr(group, key, value)
        await s.commit()
        logger.debug(f"Group {group_id} successfully updated!")
        await s.refresh(group)
        return GroupSchema.model_validate(group, from_attributes=True) if group else None
      else:
        logger.debug(f"Group with uid={group_id} not found.")
  except Exception as e:
    logger.exception(f"Error updating group {group_id}: {e}")
    return None

async def del_group(group_id: int):
  try:
    async with session() as s:
      stmt = select(Groups).where(Groups.uid == group_id)
      group = s.execute(stmt).scalar_one_or_none()
      if group:
        s.delete(group)
        await s.commit()
      else:
        logger.debug(f"Group with uid={group_id} not found.")
  except Exception as e:
    logger.exception(f"Error deleting group {group_id}: {e}")
    return None

async def get_group_by_id(group_id: int):
  try:
    async with session() as s:
      stmt = select(Groups).where(Groups.uid == group_id)
      result = await s.execute(stmt)
      group = result.scalar_one_or_none()
      return GroupSchema.model_validate(group, from_attributes=True) if group else None
  except Exception as e:
    logger.exception(f"Error getting group by ID {group_id}: {e}")
    return None
  
async def get_group_by_name(group_name: str):
  try:
    async with session() as s:
      stmt = select(Groups).where(Groups.name == group_name)
      result = await s.execute(stmt)
      group = result.scalar_one_or_none()
      return GroupSchema.model_validate(group, from_attributes=True) if group else None
  except Exception as e:
    logger.exception(f"Error getting group by name {group_name}: {e}")
    return None
  

async def get_all_groups(*filters):
  try:
    async with session() as s:
      stmt = select(Groups)
      if filters:
        stmt = stmt.where(and_(*filters))
        
      result = await s.execute(stmt)
      groups = result.scalars().all()
      groups = [GroupSchema.model_validate(group, from_attributes=True) for group in groups]
      return groups
  except Exception as e:
    logger.exception(f"Error getting all groups: {e}")
    return None