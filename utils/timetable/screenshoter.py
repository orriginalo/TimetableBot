from datetime import datetime, timedelta
import time
from aiogram.types import FSInputFile, Message
from utils.log import logger
from PIL import Image
import variables as var
import os
from datetime import datetime, timedelta
from aiogram.types import FSInputFile, Message
from utils.log import logger
from PIL import Image
import variables as var
import bot.keyboards as kb

from utils.selenium_driver import driver_pool

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

margin = 15
CACHE_DURATION = timedelta(minutes=7)

def keep_only_day(driver, target_day):
    target_day = target_day.strip().lower()
    rows = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "row"))
    )
    
    has_lessons = False
    
    for row in rows:
        try:
            header = row.find_element(By.XPATH, ".//div[@class='table-header-col']/div")
            header_text = header.text.split()[0].strip().lower()
            
            if header_text == target_day:
                # Проверяем наличие пар
                lessons = row.find_elements(By.XPATH, ".//div[@class='table-col']")
                for lesson in lessons:
                    content = lesson.find_element(By.XPATH, "./div[2]").text.strip()
                    if content != "-":
                        has_lessons = True
                        break
                
                # Если есть хотя бы одна пара - оставляем строку
                if has_lessons:
                    continue
                else:
                    driver.execute_script("arguments[0].remove();", row)
                    return False
            else:
                driver.execute_script("arguments[0].remove();", row)
        except:
            continue
    
    return has_lessons

async def screenshot_timetable(message: Message, group_name: str, other_group: bool = False):
    driver = await driver_pool.acquire()
    
    try:
        logger.debug(f"Started screenshotting timetable for group {group_name} (текущая неделя)...")
        week_num = var.calculate_current_study_number_week()
        monday_of_week = var.get_monday_of_week(week_num).strftime("%d.%m.%y")
        screenshot_path = f"./data/screenshots/full_{group_name.lower()}_{monday_of_week}.png"

        # Проверка существования файла и времени его последней модификации
        if os.path.exists(screenshot_path):
            last_modified_time = datetime.fromtimestamp(os.path.getmtime(screenshot_path))
            if datetime.now() - last_modified_time < CACHE_DURATION:
                logger.debug(f"Using cached screenshot: {screenshot_path}")
                try:
                    photo = FSInputFile(screenshot_path)
                    await message.answer_photo(photo=photo, caption=f"<code>{group_name.capitalize()}</code>. <b>{week_num}</b> неделя", parse_mode="html")
                except Exception as e:
                    await status_message.edit_text(f"❌ Ошибка при отправке. Попробуйте еще раз.")
                    logger.error(f"Ошибка при отправке скриншота: {e}")
                return screenshot_path

        status_message = await message.answer("⏳ Проверяю расписание...")

        parent_container = await driver.select_timetable(group_name, next_week=False)
        if parent_container is None:
            if other_group:
                await status_message.delete()
                await message.answer(f"📭 <b>Расписания на текущую неделю нет</b>.", parse_mode="html", reply_markup=kb.main_keyboard) 
                logger.warning(f"Текущая неделя для группы {group_name} не найдена.")
                return None
            else:
                await status_message.edit_text(f"📭 <b>Расписания на текущую неделю нет</b>.", parse_mode="html") 
                logger.warning(f"Текущая неделя для группы {group_name} не найдена.")
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
            await status_message.edit_text("⏳ Отправляю...")
            await message.answer_photo(photo=photo, caption=f"<code>{group_name.capitalize()}</code>. <b>{week_num}</b> неделя", parse_mode="html")
            await status_message.delete()
        except Exception as e:
            await status_message.edit_text(f"❌ Ошибка при отправке. Попробуйте еще раз.")
            logger.error(f"Ошибка при отправке скриншота: {e}")

        return screenshot_path
    finally:
        await driver_pool.release(driver)


async def screenshot_timetable_next_week(message: Message, group_name: str):
    driver = await driver_pool.acquire()
    
    try:
        logger.debug(f"Started screenshotting timetable for group {group_name} (текущая неделя)...")
        week_num = var.calculate_current_study_number_week() + 1
        monday_of_week = var.get_monday_of_week(week_num).strftime("%d.%m.%y")
        screenshot_path = f"./data/screenshots/nextweek_{group_name.lower()}_{monday_of_week}.png"

        # Проверка существования файла и времени его последней модификации
        if os.path.exists(screenshot_path):
            last_modified_time = datetime.fromtimestamp(os.path.getmtime(screenshot_path))
            if datetime.now() - last_modified_time < CACHE_DURATION:
                logger.debug(f"Using cached screenshot: {screenshot_path}")
                try:
                    photo = FSInputFile(screenshot_path)
                    await message.answer_photo(photo=photo, caption=f"<code>{group_name.capitalize()}</code>. <b>{week_num}</b> неделя", parse_mode="html", reply_markup=kb.main_keyboard)
                except Exception as e:
                    await status_message.edit_text(f"❌ Ошибка при отправке. Попробуйте еще раз.")
                    logger.error(f"Ошибка при отправке скриншота: {e}")
                return screenshot_path

        status_message = await message.answer("⏳ Проверяю расписание...")

        parent_container = await driver.select_timetable(group_name, next_week=True)
        if parent_container is None:
            await status_message.delete()
            await message.answer(f"📭 <b>Расписания на следующую неделю нет</b>.", parse_mode="html") 
            logger.warning(f"Следующая неделя для группы {group_name} не найдена.")
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
            await status_message.edit_text("⏳ Отправляю...")
            await message.answer_photo(photo=photo, caption=f"<code>{group_name.capitalize()}</code>. <b>{week_num}</b> неделя", parse_mode="html", reply_markup=kb.main_keyboard)
            await status_message.delete()
        except Exception as e:
            await status_message.edit_text(f"❌ Ошибка при отправке. Попробуйте еще раз.")
            logger.error(f"Ошибка при отправке скриншота: {e}")

        return screenshot_path
    finally:
        await driver_pool.release(driver)

async def screenshot_timetable_tomorrow(message: Message, group_name: str):
    driver = await driver_pool.acquire()
    
    try:
        logger.debug(f"Started screenshotting tomorrow timetable for {group_name}")
        
        # Определяем дату завтра и форматируем для поиска
        now = datetime.now()
        tomorrow_date = now + timedelta(days=1)
        tomorrow_str = tomorrow_date.strftime("%d.%m.%y")
        target_date = tomorrow_date.strftime("%d %B").lower()
        
        screenshot_path = f"./data/screenshots/tomorrow_{group_name.lower()}_{tomorrow_str}.png"
        # os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)

        if os.path.exists(screenshot_path):
            last_modified_time = datetime.fromtimestamp(os.path.getmtime(screenshot_path))
            if datetime.now() - last_modified_time < CACHE_DURATION:
                logger.debug(f"Using cached screenshot: {screenshot_path}")
                try:
                    photo = FSInputFile(screenshot_path)
                    await message.answer_photo(photo=photo, caption=f"🗓️ Расписание на завтра <i>({tomorrow_str})</i>", parse_mode="html")
                except Exception as e:
                    await status_message.edit_text(f"❌ Ошибка при отправке. Попробуйте еще раз.")
                    logger.error(f"Ошибка при отправке скриншота: {e}")
                return screenshot_path

        status_message = await message.answer("⏳ Проверяю расписание...")

        try:
            # Определяем нужно ли грузить следующую неделю
            next_week = tomorrow_date.weekday() == 0  # Понедельник = следующая неделя
            parent_container = await driver.select_timetable(group_name, next_week=next_week)
            
            if parent_container is None:
                await status_message.edit_text("📭 <b>Завтра нет пар.</b>", parse_mode="html")
                return None


            # Дополнительная очистка интерфейса
            driver.execute_script("""
                document.querySelector('nav.navbar')?.remove();
                document.querySelector('.input-group')?.remove();
                document.querySelector('.layout-panel')?.remove();
                document.querySelector('.week')?.remove();
            """)

            # Прокрутка и скриншот
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});", parent_container)
            time.sleep(0.5)
            
            
            tomorrow_weekday = (datetime.today()+timedelta(days=1)).weekday()
            target_day = var.weekdays[tomorrow_weekday]
            
            has_lessons = keep_only_day(driver, target_day)
            if not has_lessons:
                await status_message.edit_text("📭 <b>Завтра нет пар.</b>", parse_mode="html")
                return None
            
            # Сохранение и обрезка скриншота
            driver.save_screenshot(screenshot_path)
            
            # Обрезка изображения
            rect = parent_container.rect
            margin = 10
            crop_box = (
                max(0, int(rect['x']) - margin),
                max(0, int(rect['y']) - margin),
                int(rect['x'] + rect['width'] + margin),
                int(rect['y'] + rect['height'] + margin)
            )
            
            with Image.open(screenshot_path) as img:
                cropped = img.crop(crop_box)
                cropped.save(screenshot_path)

            # Отправка результата
            await message.answer_photo(
                photo=FSInputFile(screenshot_path),
                caption=f"🗓️ Расписание на завтра <i>({tomorrow_str})</i>",
                parse_mode="html"
            )
            await status_message.delete()

        except Exception as e:
            await status_message.edit_text(f"❌ Ошибка при отправке. Попробуйте еще раз.")
            logger.error(f"Error in tomorrow screenshot: {str(e)}")

        return screenshot_path
    finally:
        await driver_pool.release(driver)

async def screenshot_timetable_today(message: Message, group_name: str):
    driver = await driver_pool.acquire()
    
    try:
        logger.debug(f"Started screenshotting today timetable for {group_name}")
        
        # Определяем дату завтра и форматируем для поиска
        today = datetime.now()
        today_str = today.strftime("%d.%m.%y")
        
        screenshot_path = f"./data/screenshots/tomorrow_{group_name.lower()}_{today_str}.png"
        # os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)

        if os.path.exists(screenshot_path):
            last_modified_time = datetime.fromtimestamp(os.path.getmtime(screenshot_path))
            if datetime.now() - last_modified_time < CACHE_DURATION:
                logger.debug(f"Using cached screenshot: {screenshot_path}")
                try:
                    photo = FSInputFile(screenshot_path)
                    await message.answer_photo(photo=photo, caption=f"🗓️ Расписание на сегодня <i>({today_str})</i>", parse_mode="html")
                except Exception as e:
                    await status_message.edit_text(f"❌ Ошибка при отправке. Попробуйте еще раз.")
                    logger.error(f"Ошибка при отправке скриншота: {e}")
                return screenshot_path

        status_message = await message.answer("⏳ Проверяю расписание...")

        try:
            # Определяем нужно ли грузить следующую неделю
            next_week = today.weekday() == 0  # Понедельник = следующая неделя
            parent_container = await driver.select_timetable(group_name, next_week=next_week)
            
            if parent_container is None:
                await status_message.edit_text("📭 <b>Сегодня нет пар.</b>", parse_mode="html")
                return None


            # Дополнительная очистка интерфейса
            driver.execute_script("""
                document.querySelector('nav.navbar')?.remove();
                document.querySelector('.input-group')?.remove();
                document.querySelector('.layout-panel')?.remove();
                document.querySelector('.week')?.remove();
            """)

            # Прокрутка и скриншот
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});", parent_container)
            time.sleep(0.5)
            
            
            tomorrow_weekday = datetime.today().weekday()
            target_day = var.weekdays[tomorrow_weekday]
            
            has_lessons = keep_only_day(driver, target_day)
            if not has_lessons:
                await status_message.edit_text("📭 <b>Сегодня нет пар.</b>", parse_mode="html")
                return None
            
            # Сохранение и обрезка скриншота
            driver.save_screenshot(screenshot_path)
            
            # Обрезка изображения
            rect = parent_container.rect
            margin = 10
            crop_box = (
                max(0, int(rect['x']) - margin),
                max(0, int(rect['y']) - margin),
                int(rect['x'] + rect['width'] + margin),
                int(rect['y'] + rect['height'] + margin)
            )
            
            with Image.open(screenshot_path) as img:
                cropped = img.crop(crop_box)
                cropped.save(screenshot_path)

            # Отправка результата
            await message.answer_photo(
                photo=FSInputFile(screenshot_path),
                caption=f"🗓️ Расписание на сегодня <i>({today_str})</i>",
                parse_mode="html"
            )
            await status_message.delete()

        except Exception as e:
            await status_message.edit_text(f"❌ Ошибка при отправке. Попробуйте еще раз.")
            logger.error(f"Error in today screenshot: {str(e)}")

        return screenshot_path
    finally:
        await driver_pool.release(driver)