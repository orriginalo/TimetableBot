from sqlalchemy import Boolean, cast, func
from bot.database.models import User
from bot.database.queries.group import get_group_by_name
from bot.database.queries.user import get_user_by_id, get_users
from bot.database.queries.settings import get_setting, set_setting
from utils.timetable.downloader import download_timetable
from utils.log import logger
from aiogram.types import FSInputFile, InputMediaPhoto
from utils.selenium_driver import driver
from aiogram import Bot
from datetime import datetime, timedelta
from rich import print
import pdfplumber
import os
import requests
from bs4 import BeautifulSoup
import re
from utils.log import logger
import bot.keyboards as kb
from pdf2image import convert_from_path

async def check_changes_job(bot: Bot):
  global already_sended
  pdf_url = get_pdf_url_from_page()
  download_pdf_from_url(pdf_url)
  filename = check_if_exists_changes_pdf_to_tomorrow()
  last_send_date = await get_setting("last_send_changes_date")
  if filename is not None:
    if last_send_date is None or last_send_date != datetime.today().strftime("%d.%m.%y"):
      last_send_date = datetime.today().strftime("%d.%m.%y")
      logger.info(f"Changes for tomorrow found: {filename}")
      await set_setting("last_send_changes_date", last_send_date)
      await send_changes_to_users(bot, get_changes_date(filename))
    
def pdf_to_png(pdf_path: str, output_folder: str, date: str):
    # Конвертируем PDF в список изображений (по одной картинке на страницу)
    # images = convert_from_path(pdf_path, dpi=300)
    images = convert_from_path(pdf_path, dpi=300, poppler_path="C:\\poppler\\poppler-24.08.0\\Library\\bin")

    # Сохраняем каждую страницу как PNG
    for i, img in enumerate(images):
      img_path = f"{output_folder}/{date}_{i+1}.png"
      if not os.path.exists(img_path):
        img.save(img_path, "PNG")
  
    
def check_if_exists_changes_pdf_to_tomorrow():
  path_to_files = "./data/changes"
  files = os.listdir(path_to_files)
  
  today_date = datetime.today().strftime("%d.%m.%y")
  tomorrow_date = (datetime.today() + timedelta(days=1)).strftime("%d.%m.%y")
  
  for file in files:
    if file.endswith(".pdf"):
      file_date = file.replace("changes_", "").replace(".pdf", "")
      if file_date == tomorrow_date or file_date == today_date:
        return file
  return None

def download_pdf_from_url(url: str):
  changes_date = get_changes_date(url)
  
  if not url:
    logger.error("PDF file not found.")
    return
  else:
    logger.debug(f"URL to the PDF file found: {url}")

  response = requests.get(url)
  if response.status_code != 200:
    logger.error(f"Failed to download the PDF file. Status code: {response.status_code}")
    return
  
  path_to_file = f"./data/changes/changes_{changes_date}.pdf"
  with open(path_to_file, 'wb') as f:
    f.write(response.content)
  logger.debug(f"PDF file is successfully saved as {path_to_file}")


async def send_changes_to_users(bot: Bot, date: str):
  logger.info("Sending changes to users")

  users_with_setting = await get_users(User.settings['send_changes_updated'].as_boolean() == True)
  
  files = []
  today_date = datetime.today().strftime('%d.%m.%y')
  tomorrow_date = (datetime.today() + timedelta(days=1)).strftime('%d.%m.%y')
  
  # Конвертируем PDF в PNG
  pdf_to_png(f"./data/changes/changes_{date}.pdf", f"./data/changes/", date)

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
      f"Группа <code>{user["group_name"].capitalize()}</code> <b>есть</b> в списке изменений!"
    ) if check_if_group_in_changes(group["name"], date) else (
      f"🔔 Появились изменения на <b>{date}</b>.\n"
      f"Группы <code>{user["group_name"].capitalize()}</code> <b>нет</b> в списке изменений."
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
  

async def instantly_send_changes(bot: Bot, user: dict):
  message = await bot.send_message(user["tg_id"], "⏳ Получаю изменения...", parse_mode="html")
  files = os.listdir("./data/changes/")
  files.sort()
  png_files = []
  changes_date = None
  for f in files:
    if f.endswith(".pdf"):
      changes_date = f.replace(".pdf", "").replace("changes_", "")
      for f2 in files:
        if changes_date in f2 and f2.endswith(".png"):
          png_files.append(f2)
      break
    
  media = [InputMediaPhoto(media=FSInputFile(f"./data/changes/{f}")) for f in png_files]
  
  await message.edit_text("⏳ Проверяю...")
  is_group_in_changes = check_if_group_in_changes(user["group_name"], changes_date)
  
  if not is_group_in_changes:
    await message.delete()
    await bot.send_message(user["tg_id"],
                           f"Группы <code>{user["group_name"].capitalize()}</code> <b>нет</b> в списке изменений.\n"
                           f"Посмотреть изменения?",
                           parse_mode="html",
                           reply_markup=kb.ask_changes_keyboard)
  else:
    await message.edit_text("⏳ Отправляю...")
    text = f"Изменения на <b>{changes_date}</b>.\n" + f"Группа <code>{user["group_name"].capitalize()}</code> <b>есть</b> в списке изменений!"
    if len(media) == 1:
        await bot.send_photo(user["tg_id"], photo=files[0], caption=text,parse_mode="html")
    elif len(media) > 1:
      media[0].caption = text
      media[0].parse_mode = "html"
      await bot.send_media_group(user["tg_id"], media=media)
    await message.delete()
  
  
def check_if_group_in_changes(group_name: str, date: str):
  group_name = group_name.lower()
  with pdfplumber.open(f"./data/changes/changes_{date}.pdf") as pdf:
    for page in pdf.pages:
      text = page.extract_text().lower()
      text = text.splitlines()
      for line in text:
        if group_name in line and ("прием" not in line) and ("подготовка" not in line) and ("пересдача" not in line) and ("консультация" not in line) and ("профориентационное" not in line):
          return True
  return False
          

def get_changes_date(url: str):

    file_name = url.split('/')[-1]
    date_match = re.search(r'\d{2}\.\d{2}\.\d{2}', file_name)

    if date_match:
      date = date_match.group(0)
      return date
    else:
      logger.debug(f"Date not found in the file name: {file_name}")
      return None

def get_pdf_url_from_page():
    url = "https://ulstu.ru/education/kei/student/schedule/"

    logger.debug(f"Getting a page with URL: {url}")
    response = requests.get(url)
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
