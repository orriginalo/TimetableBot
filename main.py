import asyncio
import os
from dotenv import load_dotenv

from utils.log import logger
from bot.handlers import router

from aiogram import Bot, Dispatcher

load_dotenv()

TOKEN = os.getenv('API_KEY')

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def main():
  dp.include_router(router)

  logger.info('Bot started')
  await dp.start_polling(bot)
    
if __name__ == '__main__':
  try:
    asyncio.run(main())
  except KeyboardInterrupt:
    logger.info('Bot stopping...')