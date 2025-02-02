from datetime import datetime, timedelta
import time
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
import bot.keyboards as kb

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
    
    for row in rows:
        try:
            header = row.find_element(By.XPATH, ".//div[@class='table-header-col']")
            header_text = header.text
            
            if target_day in header_text.lower() or header_text.lower().startswith("пара"):
                continue  # Оставляем эту строку
            else:
                # Удаляем строки с другими днями
                driver.execute_script("arguments[0].remove();", row)
        except:
            # Пропускаем строки без заголовка дня
            continue

async def screenshot_timetable(message: Message, driver: Driver, group_name: str, other_group: bool = False):
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

    parent_container = driver.select_timetable(group_name, next_week=False)
    if parent_container is None:
        if other_group:
            await status_message.delete()
            await message.answer(f"📭 <b>Расписания на текущую неделю нет</b>.", parse_mode="html", reply_markup=kb.main_keyboard) 
            logger.error(f"Текущая неделя для группы {group_name} не найдена.")
            return None
        else:
            await status_message.edit_text(f"📭 <b>Расписания на текущую неделю нет</b>.", parse_mode="html") 
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
        await status_message.edit_text("⏳ Отправляю...")
        await message.answer_photo(photo=photo, caption=f"<code>{group_name.capitalize()}</code>. <b>{week_num}</b> неделя", parse_mode="html")
        await status_message.delete()
    except Exception as e:
        await status_message.edit_text(f"❌ Ошибка при отправке. Попробуйте еще раз.")
        logger.error(f"Ошибка при отправке скриншота: {e}")

    return screenshot_path


async def screenshot_timetable_next_week(message: Message, driver: Driver, group_name: str):
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
                await message.answer_photo(photo=photo, caption=f"<code>{group_name.capitalize()}</code>. <b>{week_num}</b> неделя", parse_mode="html", reply_markup=kb.main_keyboard)
            except Exception as e:
                await status_message.edit_text(f"❌ Ошибка при отправке. Попробуйте еще раз.")
                logger.error(f"Ошибка при отправке скриншота: {e}")
            return screenshot_path

    status_message = await message.answer("⏳ Проверяю расписание...")

    parent_container = driver.select_timetable(group_name, next_week=True)
    if parent_container is None:
        await status_message.delete()
        await message.answer(f"📭 <b>Расписания на следующую неделю нет</b>.", parse_mode="html") 
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
        await status_message.edit_text("⏳ Отправляю...")
        await message.answer_photo(photo=photo, caption=f"<code>{group_name.capitalize()}</code>. <b>{week_num}</b> неделя", parse_mode="html", reply_markup=kb.main_keyboard)
        await status_message.delete()
    except Exception as e:
        await status_message.edit_text(f"❌ Ошибка при отправке. Попробуйте еще раз.")
        logger.error(f"Ошибка при отправке скриншота: {e}")

    return screenshot_path

async def screenshot_timetable_tomorrow(message: Message, driver: Driver, group_name: str):
    logger.debug(f"Started screenshotting tomorrow timetable for {group_name}")
    
    # Определяем дату завтра и форматируем для поиска
    now = datetime.now()
    tomorrow_date = now + timedelta(days=1)
    tomorrow_str = tomorrow_date.strftime("%d.%m.%y")
    target_date = tomorrow_date.strftime("%d %B").lower()
    
    screenshot_path = f"./data/screenshots/tomorrow_{group_name.lower()}_{tomorrow_str}.png"
    # os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)

    status_message = await message.answer("⏳ Проверяю расписание...")

    try:
        # Определяем нужно ли грузить следующую неделю
        next_week = tomorrow_date.weekday() == 0  # Понедельник = следующая неделя
        parent_container = driver.select_timetable(group_name, next_week=next_week)
        
        if parent_container is None:
            await status_message.edit_text("📭 <b>Завтра нет пар.</b>", parse_mode="html")
            return None

        # Удаляем все элементы кроме завтрашнего дня
        driver.execute_script(f"""
            // Удаляем заголовки недель
            document.querySelector('.week')?.remove();
            document.querySelector('.week-num')?.remove();
            
            // Находим все строки с днями
            const allRows = Array.from(document.querySelectorAll('.row'));
            
            // Оставляем только строку с завтрашней датой
            let targetRow = null;
            for(const row of allRows) {{
                const header = row.querySelector('.table-header-col');
                if(header && header.textContent.toLowerCase().includes("{target_date}")) {{
                    targetRow = row;
                    break;
                }}
            }}
            
            // Удаляем все другие строки
            if(targetRow) {{
                const container = targetRow.closest('.container');
                while(container.firstChild) container.removeChild(container.firstChild);
                container.appendChild(targetRow);
            }}
            
            // Удаляем пустые колонки
            document.querySelectorAll('.table-col').forEach(col => {{
                if(col.textContent.trim() === '-') col.remove();
            }});
        """)

        # Дополнительная очистка интерфейса
        driver.execute_script("""
            document.querySelector('nav.navbar')?.remove();
            document.querySelector('.input-group')?.remove();
            document.querySelector('.layout-panel')?.remove();
        """)

        # Прокрутка и скриншот
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});", parent_container)
        time.sleep(0.5)
        
        
        tomorrow_weekday = (datetime.today()+timedelta(days=1)).weekday()
        target_day = var.weekdays[tomorrow_weekday]
        print(target_day)
        
        keep_only_day(driver, target_day)
        
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
            caption=f"Расписание {group_name} на {tomorrow_str}"
        )
        await status_message.delete()

    except Exception as e:
        await status_message.edit_text(f"❌ Ошибка при отправке. Попробуйте еще раз.")
        logger.error(f"Error in tomorrow screenshot: {str(e)}")

    return screenshot_path