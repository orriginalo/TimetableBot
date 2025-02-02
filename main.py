import asyncio
import os
from dotenv import load_dotenv

from utils.log import logger
from bot.handlers import router
from bot.database.core import create_tables
from bot.scheduler import start_scheduler
from utils.selenium_driver import driver
from bot.middlewares import CheckState, MsgLoggerMiddleware

from aiogram import Bot, Dispatcher

load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')

bot = Bot(token=TOKEN)
dp = Dispatcher()

dp.message.middleware(MsgLoggerMiddleware())
dp.message.filter(CheckState())

login = os.getenv('LOGIN')
password = os.getenv('PASSWORD')

async def create_data_directory():
    folders = [
        "./data/changes",
        "./data/screenshots",
        "./data/database",
        "./data/logs",
    ]
    counter: int = 0
    for folder in folders:
      if not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)
        counter += 1
        logger.debug(f"Data directory created: {folder}")
    return counter

async def main():
  created_folders_count = await create_data_directory()
  logger.info(f"Data directory checked (total {created_folders_count} folders created)")
  
  driver.auth(login, password)
  logger.info("Driver authenticated")
  
  await create_tables(drop_tables=True, populate_groups=True)
  logger.info("Database tables created")
  
  await start_scheduler(bot)
  logger.info("Scheduler started")

  dp.include_router(router)
  logger.info("Router included")

  logger.info('Bot started')
  await dp.start_polling(bot)
    
if __name__ == '__main__':
  try:
    asyncio.run(main())
  except KeyboardInterrupt:
    logger.info('Bot stopping...')