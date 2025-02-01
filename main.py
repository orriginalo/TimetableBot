import asyncio
import os
from dotenv import load_dotenv

from utils.log import logger
from bot.handlers import router
from bot.database.core import create_tables
from bot.scheduler import start_scheduler
from utils.selenium_driver import driver
from bot.middlewares import MsgLoggerMiddleware

from aiogram import Bot, Dispatcher

load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')

bot = Bot(token=TOKEN)
dp = Dispatcher()

dp.message.middleware(MsgLoggerMiddleware())

login = os.getenv('LOGIN')
password = os.getenv('PASSWORD')

async def main():
  driver.auth(login, password)
  logger.info("Driver authenticated")
  
  await create_tables(drop_tables=False, populate_groups=False)
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