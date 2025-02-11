from datetime import datetime, timedelta
import aiohttp
import asyncio
import os
from dotenv import load_dotenv
from aiogram.types import Message, FSInputFile
# from utils.log import logger

load_dotenv(override=True)

async def fetch_screenshot_path_and_send(group_name: str, period: str, msg: Message):
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
              caption: str = None
              week_num = (decoded_line[5:].split("|"))[1]
              if period in ["full", "nextweek"]:
                caption = f"<code>{group_name.capitalize()}</code>. <b>{week_num}</b> неделя"
              elif period == "today":
                today = datetime.now().strftime("%d.%m.%y")
                caption = f"🗓️ Расписание на сегодня <i>({today})</i>"
              elif period == "tomorrow":
                tomorrow = (datetime.now() + timedelta(days=1)).strftime("%d.%m.%y")
                caption = f"🗓️ Расписание на завтра <i>({tomorrow})</i>"
              
              await msg.answer_photo(FSInputFile(decoded_line[5:-(len(decoded_line.split("|")[1])+1)].strip()), caption=caption if caption else "", parse_mode="html")
              await sent_message.delete()
              return
            if decoded_line.startswith("data:"):
              progress = decoded_line[6:].strip()
              await sent_message.edit_text(f"{progress}", parse_mode="html")
  except Exception as e:
    await sent_message.edit_text("🚫 Не удалось получить расписание. Попробуйте позже.")
    print(e)
    return
  
async def get_screenshot_path(group_name: str, period: str):
  url = f"{os.getenv('API_URL')}/screenshots/{group_name}/{period}"
  async with aiohttp.ClientSession() as session:
    async with session.get(url) as response:
      async for line in response.content:
        if line:
          decoded_line = line.decode("utf-8").strip().replace("\n", "")
          if decoded_line.startswith("end:"):
            return decoded_line[5:-(len(decoded_line.split("|")[1])+1)].strip()
      
# async def main():
#   group = "пдо-16"
#   path = await get_screenshot_path(group, "nextweek")
#   print(path)
  
# asyncio.run(main())