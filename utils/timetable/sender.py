from datetime import datetime, timedelta
import os
from aiogram.types import FSInputFile
from bot.database.models import User
from bot.database.queries.group import get_group_by_name
from bot.database.queries.user import get_users
from utils.log import logger
from utils.selenium_driver import driver
import variables as var
from aiogram import Bot
from PIL import Image

margin = 15
CACHE_DURATION=timedelta(minutes=7)

async def send_new_timetable(bot: Bot):
    logger.info("Sending timetable to next week...")

    users_with_notifications = await get_users(User.settings['send_timetable_new_week'].as_boolean() == True)
    print(users_with_notifications)
    groups: set = set()
    for user in users_with_notifications:
      groups.add((await get_group_by_name(user['group_name']))["name"])

    groups = list(groups)
    print(groups)
    for user in users_with_notifications:
      group_name = user["group_name"]
      logger.debug(f"Started screenshotting timetable for group {group_name} (текущая неделя)...")
      week_num = var.calculate_current_study_number_week() + 1
      monday_of_week = var.get_monday_of_week(week_num).strftime("%d.%m.%y")
      screenshot_path = f"./data/screenshots/full_{group_name.lower()}_{monday_of_week}.png"

      # Проверка существования файла и времени его последней модификации
      if os.path.exists(screenshot_path):
          last_modified_time = datetime.fromtimestamp(os.path.getmtime(screenshot_path))
          if datetime.now() - last_modified_time < CACHE_DURATION:
              logger.debug(f"Using cached screenshot: {screenshot_path}")
              try:
                  photo = FSInputFile(screenshot_path)
                  await bot.send_photo(user["tg_id"], photo=photo, caption=f"<code>{group_name.capitalize()}</code>. <b>{week_num}</b> неделя", parse_mode="html")
                  return
              except Exception as e:
                  logger.error(f"Ошибка при отправке скриншота: {e}")
                  return

      parent_container = driver.select_timetable(user["group_name"], next_week=True)
      photo = FSInputFile(f"./data/screenshots/{user["group_name"]}.png")
      await bot.send_photo(user["tg_id"], photo, caption="🔔 Расписание на следующую неделю")
      
      driver.save_screenshot(screenshot_path)

      rect = parent_container.rect
      crop_box = (
          max(0, int(rect['x']) - margin),
          max(0, int(rect['y']) - margin),
          int(rect['x'] + rect['width'] + margin),
          int(rect['y'] + rect['height'] + margin)
      )
      image = Image.open(screenshot_path)
      cropped_image = image.crop(crop_box)
      cropped_image.save(screenshot_path)
      logger.debug(f"Screenshot saved: {screenshot_path}")

      try:
          photo = FSInputFile(screenshot_path)
          await bot.send_photo(user["tg_id"], photo=photo, caption=f"🔔 Расписание на следующую неделю", parse_mode="html")
      except Exception as e:
          logger.error(f"Ошибка при отправке скриншота: {e}")

      return screenshot_path