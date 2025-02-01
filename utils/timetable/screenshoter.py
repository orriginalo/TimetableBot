from datetime import datetime, timedelta
from aiogram import Bot
from aiogram.types import FSInputFile, Message
from utils.selenium_driver import Driver
from utils.log import logger
from PIL import Image
import variables as var
import os
from datetime import datetime, timedelta
from aiogram.types import FSInputFile, Message
from utils.selenium_driver import Driver
from utils.log import logger
from PIL import Image
import variables as var

margin = 15
CACHE_DURATION = timedelta(minutes=30)

async def screenshot_timetable(message: Message, driver: Driver, group_name: str):
    logger.debug(f"Started screenshotting timetable for group {group_name} (текущая неделя)...")
    monday_of_week = var.get_monday_of_week(var.calculate_current_study_number_week()).strftime("%d.%m.%y")
    screenshot_path = f"./data/screenshots/full_{group_name.lower()}_{monday_of_week}.png"

    # Проверка существования файла и времени его последней модификации
    if os.path.exists(screenshot_path):
        last_modified_time = datetime.fromtimestamp(os.path.getmtime(screenshot_path))
        if datetime.now() - last_modified_time < CACHE_DURATION:
            logger.debug(f"Using cached screenshot: {screenshot_path}")
            try:
                photo = FSInputFile(screenshot_path)
                await message.answer_photo(photo=photo, caption=f"Расписание для группы {group_name} (текущая неделя)")
            except Exception as e:
                await message.answer(f"Ошибка при отправке скриншота: {e}")
                logger.error(f"Ошибка при отправке скриншота: {e}")
            return screenshot_path

    status_message = await message.answer("Начинаю создание скриншота...")

    parent_container = driver.select_timetable(group_name, next_week=False)
    if parent_container is None:
        await status_message.edit_text(f"Текущая неделя для группы {group_name} не найдена.")
        logger.error(f"Текущая неделя для группы {group_name} не найдена.")
        return None

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
        await status_message.edit_text("Отправляю скриншот...")
        await message.answer_photo(photo=photo, caption=f"Расписание для группы {group_name} (текущая неделя)")
        await status_message.delete()
    except Exception as e:
        await status_message.edit_text(f"Ошибка при отправке скриншота: {e}")
        logger.error(f"Ошибка при отправке скриншота: {e}")

    return screenshot_path


async def screenshot_timetable_next_week(message: Message, driver: Driver, group_name: str):
    logger.debug(f"Started screenshotting timetable for group {group_name} (текущая неделя)...")
    monday_of_week = var.get_monday_of_week(var.calculate_current_study_number_week() + 1).strftime("%d.%m.%y")
    screenshot_path = f"./data/screenshots/full_{group_name.lower()}_{monday_of_week}.png"

    # Проверка существования файла и времени его последней модификации
    if os.path.exists(screenshot_path):
        last_modified_time = datetime.fromtimestamp(os.path.getmtime(screenshot_path))
        if datetime.now() - last_modified_time < CACHE_DURATION:
            logger.debug(f"Using cached screenshot: {screenshot_path}")
            try:
                photo = FSInputFile(screenshot_path)
                await message.answer_photo(photo=photo, caption=f"Расписание для группы {group_name} (следующая неделя)")
            except Exception as e:
                await message.answer(f"Ошибка при отправке скриншота: {e}")
                logger.error(f"Ошибка при отправке скриншота: {e}")
            return screenshot_path

    status_message = await message.answer("Начинаю создание скриншота...")

    parent_container = driver.select_timetable(group_name, next_week=True)
    if parent_container is None:
        await status_message.edit_text(f"Текущая неделя для группы {group_name} не найдена.")
        logger.error(f"Следующая неделя для группы {group_name} не найдена.")
        return None

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
        await status_message.edit_text("Отправляю скриншот...")
        await message.answer_photo(photo=photo, caption=f"Расписание для группы {group_name} (следующая неделя)")
        await status_message.delete()
    except Exception as e:
        await status_message.edit_text(f"Ошибка при отправке скриншота: {e}")
        logger.error(f"Ошибка при отправке скриншота: {e}")

    return screenshot_path

async def screenshot_timetable_tomorrow(message: Message, driver: Driver, group_name: str):
    logger.debug(f"Started screenshotting timetable for group {group_name} (завтра)...")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%d.%m.%y")
    screenshot_path = f"./data/screenshots/tomorrow_{group_name.lower()}_{tomorrow}.png"

    status_message = await message.answer("Начинаю создание скриншота...")

    parent_container = driver.select_timetable(group_name, next_week=False)
    if parent_container is None:
        await status_message.edit_text(f"Расписание для группы {group_name} не найдено для текущей недели (завтра).")
        logger.error(f"Расписание для группы {group_name} не найдено для текущей недели (завтра).")
        return None

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
        await status_message.edit_text("Отправляю скриншот...")
        await message.answer_photo(photo=photo, caption=f"Расписание для группы {group_name} (завтра)")
        await status_message.delete()
    except Exception as e:
        await status_message.edit_text(f"Ошибка при отправке скриншота: {e}")
        logger.error(f"Ошибка при отправке скриншота: {e}")

    return screenshot_path
