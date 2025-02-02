import os
import re
import requests
import pdfplumber
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot
from aiogram.types import FSInputFile, InputMediaPhoto, Message
from utils.log import logger
from utils.selenium_driver import driver
from utils.timetable.downloader import download_timetable
from bot.database.models import User
from bot.database.queries.group import get_group_by_name
from bot.database.queries.user import get_user_by_id, get_users
from bot.database.queries.settings import get_setting, set_setting
from pdf2image import convert_from_path
from rich import print
from bs4 import BeautifulSoup
import bot.keyboards as kb

async def check_changes_job(bot: Bot):
    global already_sended
    pdf_url = await get_pdf_url_from_page()
    await download_pdf_from_url(pdf_url)
    filename = await check_if_exists_changes_pdf_to_tomorrow()
    last_send_date = await get_setting("last_send_changes_date")
    if filename is not None:
        if last_send_date is None or last_send_date != datetime.today().strftime("%d.%m.%y"):
            last_send_date = datetime.today().strftime("%d.%m.%y")
            logger.info(f"Changes for tomorrow found: {filename}")
            await set_setting("last_send_changes_date", last_send_date)
            await send_changes_to_users(bot, await get_changes_date(filename))

def write_pdf_to_file(path_to_file: str, content: bytes):
    with open(path_to_file, "wb") as f:
        f.write(content)

async def pdf_to_png(pdf_path: str, output_folder: str, date: str):
    # Конвертируем PDF в список изображений (по одной картинке на страницу)
    images = await asyncio.to_thread(convert_from_path, pdf_path, dpi=300, poppler_path="C:\\poppler\\poppler-24.08.0\\Library\\bin")

    # Сохраняем каждую страницу как PNG
    for i, img in enumerate(images):
        img_path = f"{output_folder}/{date}_{i+1}.png"
        if not os.path.exists(img_path):
            await asyncio.to_thread(img.save, img_path, "PNG")
  
async def check_if_exists_changes_pdf_to_tomorrow():
    path_to_files = "./data/changes"
    files = await asyncio.to_thread(os.listdir, path_to_files)
  
    today_date = datetime.today().strftime("%d.%m.%y")
    tomorrow_date = (datetime.today() + timedelta(days=1)).strftime("%d.%m.%y")
  
    for file in files:
        if file.endswith(".pdf"):
            file_date = file.replace("changes_", "").replace(".pdf", "")
            if file_date == tomorrow_date or file_date == today_date:
                return file
    return None

async def download_pdf_from_url(url: str):
    changes_date = await get_changes_date(url)
  
    if not url:
        logger.error("PDF file not found.")
        return
    else:
        logger.debug(f"URL to the PDF file found: {url}")

    response = await asyncio.to_thread(requests.get, url)
    if response.status_code != 200:
        logger.error(f"Failed to download the PDF file. Status code: {response.status_code}")
        return
  
    path_to_file = f"./data/changes/changes_{changes_date}.pdf"
    await asyncio.to_thread(write_pdf_to_file, path_to_file, response.content)
    logger.debug(f"PDF file is successfully saved as {path_to_file}")

async def send_changes_to_users(bot: Bot, date: str):
    logger.info("Sending changes to users")

    users_with_setting = await get_users(User.settings['send_changes_updated'].as_boolean() == True)
  
    files = []
    today_date = datetime.today().strftime('%d.%m.%y')
    tomorrow_date = (datetime.today() + timedelta(days=1)).strftime('%d.%m.%y')
  
    # Конвертируем PDF в PNG
    await pdf_to_png(f"./data/changes/changes_{date}.pdf", f"./data/changes/", date)

    # Собираем файлы изображений
    files_paths = []
    for f in os.listdir(f"./data/changes/"):
        if f.endswith(".png") and date in f:
            files_paths.append(f"./data/changes/{f}")
    files_paths.sort()
  
    for path in files_paths:
        files.append(FSInputFile(f"{path}"))
  

    for user in users_with_setting:
        group = await get_group_by_name(user["group_name"])
        text = (
            f"🔔 Появились изменения на <b>{date}</b>.\n"
            f"<code>{user['group_name'].capitalize()}</code> <b>есть</b> в списке изменений!"
        ) if await check_if_group_in_changes(group["name"], date) else (
            f"🔔 Появились изменения на <b>{date}</b>.\n"
            f"<code>{user['group_name'].capitalize()}</code> <b>нет</b> в списке изменений."
        )

        # Если только 1 фото → отправляем обычное `send_photo()`
        if len(files) == 1:
            await bot.send_photo(user["tg_id"], photo=files[0], caption=text, parse_mode="html")
        elif len(files) > 1:
            # Создаём `media_group`
            media = [InputMediaPhoto(media=f) for f in files]
            media[0].caption = text  # Добавляем описание только к первой картинке
            media[0].parse_mode = "html"

            await bot.send_media_group(user["tg_id"], media=media)

async def changes_to_tomorrow_exists():
    tomorrow_date = (datetime.today() + timedelta(days=1)).strftime("%d.%m.%y")
    path_to_file = f"./data/changes/changes_{tomorrow_date}.pdf"
    return os.path.exists(path_to_file)

def get_last_png_changes():

    files = os.listdir("./data/changes/")
    pdf_files = []

    # Собираем все PDF файлы и парсим даты
    for f in files:
        if f.startswith("changes_") and f.endswith(".pdf"):
            date_str = f.replace("changes_", "").replace(".pdf", "")
            try:
                date = datetime.strptime(date_str, "%d.%m.%y")
                pdf_files.append((date, f))
            except ValueError:
                continue

    # Сортируем PDF файлы по дате в убывающем порядке
    pdf_files.sort(reverse=True, key=lambda x: x[0])

    if pdf_files:
        latest_date = pdf_files[0][0].strftime("%d.%m.%y")
        
        # Ищем соответствующие PNG файлы
        png_files = [f for f in files 
                    if f.startswith(latest_date) and f.endswith(".png")]
        
        return {
            "png_files": sorted(png_files),
            "latest_date": latest_date
        }
    else:
        print("No PDF files found")
        
    return None
    


async def instantly_send_changes(msg: Message, user: dict, with_ask: bool = True):
    if with_ask:
        msg = await msg.bot.send_message(user["tg_id"], "⏳ Получаю изменения...", parse_mode="html")
    
    last_png_changes = get_last_png_changes()
    png_files = []
    changes_date = None
    
    if last_png_changes:
        png_files = last_png_changes["png_files"]
        changes_date = last_png_changes["latest_date"]
    
    media = [InputMediaPhoto(media=FSInputFile(f"./data/changes/{f}")) for f in png_files]
    
    if with_ask:
        await msg.edit_text("⏳ Проверяю...")
    is_group_in_changes = await check_if_group_in_changes(user["group_name"], changes_date)
  
    if not is_group_in_changes:
        if with_ask:
            await msg.delete()
            await msg.bot.send_message(user["tg_id"],
                                f"<code>{user['group_name'].capitalize()}</code> <b>нет</b> в списке изменений. <i>({changes_date})</i>.\n"
                                f"Показать изменения?",
                                parse_mode="html",
                                reply_markup=kb.ask_changes_keyboard)
        else:
            await msg.delete()
            text = f"Изменения на <b>{changes_date}</b>.\n" + f"<code>{user['group_name'].capitalize()}</code> <b>нет</b> в списке изменений."
            if len(media) == 1:
                await msg.bot.send_photo(user["tg_id"], photo=media[0], caption=text, parse_mode="html")
            elif len(media) > 1:
                media[0].caption = text
                media[0].parse_mode = "html"
                await msg.bot.send_media_group(user["tg_id"], media=media)
    else:
        if with_ask:
            await msg.edit_text("⏳ Отправляю...")
        text = f"Изменения на <b>{changes_date}</b>.\n" + f"<code>{user['group_name'].capitalize()}</code> <b>есть</b> в списке изменений!"
        if len(media) == 1:
            await msg.bot.send_photo(user["tg_id"], photo=media[0], caption=text, parse_mode="html")
        elif len(media) > 1:
            media[0].caption = text
            media[0].parse_mode = "html"
            await msg.bot.send_media_group(user["tg_id"], media=media)
        await msg.delete()

async def check_if_group_in_changes(group_name: str, date: str):
    group_name = group_name.lower()

    # Функция, которая будет выполняться в отдельном потоке
    def check():
        with pdfplumber.open(f"./data/changes/changes_{date}.pdf") as pdf:
            for page in pdf.pages:
                text = page.extract_text().lower()
                text = text.splitlines()
                for line in text:
                    if group_name in line and all(keyword not in line for keyword in ["прием", "подготовка", "пересдача", "консультация", "профориентационное"]):
                        print(line)
                        return True
        return False

    # Выполняем check в фоновом потоке с помощью asyncio.to_thread
    return await asyncio.to_thread(check)


async def get_changes_date(url: str):
    file_name = url.split('/')[-1]
    date_match = re.search(r'\d{2}\.\d{2}\.\d{2}', file_name)
    if date_match:
        return date_match.group(0)
    else:
        logger.debug(f"Date not found in the file name: {file_name}")
        return None

async def get_pdf_url_from_page():
    url = "https://ulstu.ru/education/kei/student/schedule/"

    logger.debug(f"Getting a page with URL: {url}")
    response = await asyncio.to_thread(requests.get, url)
    if response.status_code != 200:
        logger.error(f"It was not possible to get a page. Status code: {response.status_code}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')

    scripts = soup.find_all('script', type='application/javascript')
    for script in scripts:
        script_content = script.string
        if script_content and "PDFStart" in script_content:
            match = re.search(r"PDFStart\(['\"]([^'\"]+)['\"]\)", script_content)
            if match:
                pdf_url = match.group(1)
                full_pdf_url = requests.compat.urljoin(url, pdf_url)
                return full_pdf_url

    return None
