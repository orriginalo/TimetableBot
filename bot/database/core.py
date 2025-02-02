from bot.database.setup import sync_engine
from bot.database.setup import Base

from utils.selenium_driver import driver_pool
from utils.groups_parser import parse_groups_and_add_to_db

async def create_tables(drop_tables: bool = False, populate_groups: bool = False):
  driver = await driver_pool.acquire()
  try:
    if drop_tables:
      Base.metadata.drop_all(sync_engine)
    Base.metadata.create_all(sync_engine)
    if populate_groups:
      await parse_groups_and_add_to_db(driver)
  finally:
    await driver_pool.release(driver)