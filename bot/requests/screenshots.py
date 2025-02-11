import aiohttp
import asyncio
import os
from dotenv import load_dotenv
from aiogram.types import Message, FSInputFile
from utils.log import logger

load_dotenv(override=True)

async def fetch_screenshot_path(group_name: str, period: str, msg: Message):
  url = f"{os.getenv("API_URL")}/screenshots/{group_name}/{period}"  # Используем имя сервиса FastAPI
  sent_message = await msg.answer("👀 Проверяю расписание...", parse_mode="html")
  period_text = {
    "full": "текущую неделю",
    "nextweek": "следующую неделю",
    "today": "сегодня",
    "tomorrow": "завтра",
  }
  try:
    async with aiohttp.ClientSession() as session:
      async with session.get(url) as response:
        async for line in response.content:
          if line:
            # Строки приходят в формате: "data: сообщение\n\n"
            decoded_line = line.decode("utf-8").strip().replace("\n", "")
            if decoded_line.startswith("error:"):
              content = decoded_line[7:].strip()
              if content == "not found":
                await sent_message.edit_text(f"📭 <b>Расписания на {period_text.get(period)} нет.</b>", parse_mode="html")
                return
              return
            if decoded_line.startswith("end:"):
              await msg.answer_photo(FSInputFile(decoded_line[5:].strip()))
              await sent_message.delete()
              return
            if decoded_line.startswith("data:"):
              progress = decoded_line[6:].strip()
              await sent_message.edit_text(f"{progress}", parse_mode="html")
  except Exception as e:
    await sent_message.edit_text("🚫 Не удалось получить расписание. Попробуйте позже.")
    logger.exception(e)
    return
  # Telegram server says - Bad Request: message is not modified: specified new message content and reply markup are exactly the same as a current content and reply markup of the message
# async def main():
#   group = "пдо-16"
#   timetable = await fetch_screenshot_path(group, "full")
#   print(timetable)

# asyncio.run(main())
