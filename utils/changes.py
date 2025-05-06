import os
import re
import requests
import pdfplumber
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot
from aiogram.types import FSInputFile, InputMediaPhoto, Message
from utils.log import logger
from bot.database.models import User
from bot.database.queries.group import get_group_by_name
from bot.database.queries.user import get_users
from bot.database.queries.settings import get_setting, set_setting
from pdf2image import convert_from_path
from rich import print
from bs4 import BeautifulSoup
import bot.keyboards as kb
from aiogram.fsm.context import FSMContext


async def check_changes_job(bot: Bot):
    global already_sended
    pdf_url = await get_pdf_url_from_page()
    await download_pdf_from_url(pdf_url)
    filename = await check_if_exists_changes_pdf_to_tomorrow()
    last_send_date = await get_setting(
        "last_send_changes_date"
    )  # Дата последней отправки изменений
    latest_changes_date = await get_setting(
        "last_changes_date"
    )  # Дата последних отправленных изменений
    current_changes_date = get_last_png_changes()[
        "latest_date"
    ]  # Дата текущих изменений
    if filename is not None:
        today_date = datetime.today().strftime("%d.%m.%y")

        if (
            (last_send_date is None and latest_changes_date is None)
            or (
                last_send_date != today_date
                and current_changes_date != latest_changes_date
            )
            or (
                last_send_date == today_date
                and current_changes_date != latest_changes_date
            )
        ):
            last_send_date = datetime.today().strftime("%d.%m.%y")
            last_send_date = today_date
            logger.info(f"Changes for tomorrow found: {filename}")
            latest_changes_date = current_changes_date
            await set_setting("last_send_changes_date", last_send_date)
            await set_setting("last_changes_date", latest_changes_date)
            await send_changes_to_users(bot, latest_changes_date)
        else:
            date = get_last_png_changes()["latest_date"]
            await pdf_to_png(
                f"./data/changes/changes_{date}.pdf", "./data/changes/", date
            )


def write_pdf_to_file(path_to_file: str, content: bytes):
    with open(path_to_file, "wb") as f:
        f.write(content)


async def pdf_to_png(pdf_path: str, output_folder: str, date: str):
    # Конвертируем PDF в список изображений (по одной картинке на страницу)
    # images = await asyncio.to_thread(convert_from_path, pdf_path, dpi=300, poppler_path="C:\\poppler\\poppler-24.08.0\\Library\\bin")
    images = await asyncio.to_thread(convert_from_path, pdf_path, dpi=300)

    # Сохраняем каждую страницу как PNG
    for i, img in enumerate(images):
        img_path = f"{output_folder}/{date}_{i + 1}.png"
        await asyncio.to_thread(img.save, img_path, "PNG")
        logger.debug(f"Image saved: {img_path}")


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
        logger.error(
            f"Failed to download the PDF file. Status code: {response.status_code}"
        )
        return

    path_to_file = f"./data/changes/changes_{changes_date}.pdf"
    await asyncio.to_thread(write_pdf_to_file, path_to_file, response.content)
    logger.debug(f"PDF file is successfully saved as {path_to_file}")


async def send_changes_to_users(bot: Bot, date: str):
    logger.info("Sending changes to users")

    users_with_setting = await get_users(
        User.settings["send_changes_updated"].as_boolean() == True  # noqa: E712
    )

    # Конвертируем PDF в PNG
    await pdf_to_png(f"./data/changes/changes_{date}.pdf", "./data/changes/", date)

    for user in users_with_setting:
        group = await get_group_by_name(user.group_name)
        if group:
            is_group_in_changes, page_number = await check_if_group_in_changes(
                group.name, date
            )
            if (
                not is_group_in_changes
                and user.settings["send_changes_when_isnt_group"] == False  # noqa: E712
            ):
                continue
            text = (
                (
                    f"🔔 Появились изменения на <b>{date}</b>.\n"
                    f"<code>{user.group_name.capitalize()}</code> <b>есть</b> в списке изменений!"
                )
                if is_group_in_changes
                else (
                    f"🔔 Появились изменения на <b>{date}</b>.\n"
                    f"<code>{user.group_name.capitalize()}</code> <b>нет</b> в списке изменений."
                )
            )

            # Собираем файлы изображений
            files_paths = []
            for f in os.listdir("./data/changes/"):
                if f.endswith(".png") and date in f:
                    files_paths.append(f"./data/changes/{f}")
            files_paths.sort()

            files = [FSInputFile(f"{path}") for path in files_paths]

            if (
                user.settings["only_page_with_group_in_changes"] == True  # noqa: E712
                and is_group_in_changes
            ):
                file_to_send = next(
                    (
                        file
                        for i, file in enumerate(files)
                        if f"{date}_{page_number}" in files_paths[i]
                    ),
                    None,
                )

                if file_to_send:
                    try:
                        await bot.send_photo(
                            user.tg_id,
                            photo=file_to_send,
                            caption=text,
                            parse_mode="html",
                        )
                    except Exception as e:
                        logger.error(
                            f"Не удалось отправить изменения для {user.tg_id}: {e}"
                        )

            elif len(files) == 1:
                try:
                    await bot.send_photo(
                        user.tg_id, photo=files[0], caption=text, parse_mode="html"
                    )
                except Exception as e:
                    logger.error(
                        f"Не удалось отправить изменения для {user.tg_id}: {e}"
                    )

            elif len(files) > 1:
                try:
                    # Создаём `media_group`
                    media = [InputMediaPhoto(media=f) for f in files]
                    media[
                        0
                    ].caption = text  # Добавляем описание только к первой картинке
                    media[0].parse_mode = "html"

                    await bot.send_media_group(user.tg_id, media=media)
                except Exception as e:
                    logger.error(
                        f"Не удалось отправить изменения для {user.tg_id}: {e}"
                    )


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
        png_files = [
            f for f in files if f.startswith(latest_date) and f.endswith(".png")
        ]

        return {"png_files": sorted(png_files), "latest_date": latest_date}
    else:
        print("No PDF files found")

    return None


async def instantly_send_changes(
    msg: Message, state: FSMContext, user: dict, with_ask: bool = True
):
    if with_ask:
        msg = await msg.bot.send_message(
            user.tg_id, "⏳ Получаю изменения...", parse_mode="html"
        )

    last_png_changes = get_last_png_changes()
    png_files = []
    changes_date = None

    if last_png_changes:
        png_files = last_png_changes["png_files"]
        changes_date = last_png_changes["latest_date"]

    media = [
        InputMediaPhoto(media=FSInputFile(f"./data/changes/{f}")) for f in png_files
    ]

    if with_ask:
        await msg.edit_text("⏳ Проверяю...")
    is_group_in_changes, page_number = await check_if_group_in_changes(
        user.group_name, changes_date
    )

    text = ""
    if not is_group_in_changes:
        text = (
            f"Изменения на <b>{changes_date}</b>.\n"
            + f"<code>{user.group_name.capitalize()}</code> <b>нет</b> в списке изменений."
        )
    else:
        text = (
            f"Изменения на <b>{changes_date}</b>.\n"
            + f"<code>{user.group_name.capitalize()}</code> <b>есть</b> в списке изменений!"
        )

    await state.update_data(
        changes_data={
            "is_group_in_changes": is_group_in_changes,
            "changes_date": changes_date,
            "media": media,
            "caption": text,
            "page_number": page_number,
        }
    )

    if not is_group_in_changes:
        if with_ask:
            await msg.delete()
            await msg.bot.send_message(
                user.tg_id,
                f"<code>{user.group_name.capitalize()}</code> <b>нет</b> в списке изменений. <i>({changes_date})</i>.\n"
                f"Показать изменения?",
                parse_mode="html",
                reply_markup=kb.ask_changes_keyboard,
            )
        else:
            await msg.delete()
            if len(media) == 1:
                await msg.bot.send_photo(
                    user.tg_id, photo=media[0], caption=text, parse_mode="html"
                )
            elif len(media) > 1:
                media[0].caption = text
                media[0].parse_mode = "html"
                await msg.bot.send_media_group(user.tg_id, media=media)
    else:
        if (
            user.settings["only_page_with_group_in_changes"] == True  # noqa: E712
            and is_group_in_changes
        ):
            file_to_send = next(
                (
                    photo
                    for i, photo in enumerate(media)
                    if f"{changes_date}_{page_number}" in png_files[i]
                ),
                None,
            )
            if file_to_send:
                await msg.bot.send_photo(
                    user.tg_id,
                    photo=file_to_send.media,
                    caption=text,
                    parse_mode="html",
                )

        else:
            if with_ask:
                await msg.edit_text("⏳ Отправляю...")
            if len(media) == 1:
                await msg.bot.send_photo(
                    user.tg_id, photo=media[0], caption=text, parse_mode="html"
                )
            elif len(media) > 1:
                media[0].caption = text
                media[0].parse_mode = "html"
                await msg.bot.send_media_group(user.tg_id, media=media)
        await msg.delete()


async def check_if_group_in_changes(group_name: str, date: str):
    group_name = group_name.lower()

    # Функция, которая будет выполняться в отдельном потоке
    def check():
        with pdfplumber.open(f"./data/changes/changes_{date}.pdf") as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                text = page.extract_text().lower()
                text = text.splitlines()
                for line in text:
                    if group_name in line and all(
                        keyword not in line
                        for keyword in [
                            "прием",
                            "подготовка",
                            "пересдача",
                            "консультация",
                            "профориентационное",
                        ]
                    ):
                        return True, i
        return False, 0

    # Выполняем check в фоновом потоке с помощью asyncio.to_thread
    return await asyncio.to_thread(check)


# async def get_changes_date(url: str):
#     file_name = url.split("/")[-1]
#     match = re.search(r"(\d{1,2})[- ]([a-zа-яё]+)", file_name.lower())

#     MONTHS_RU = {
#         "yanvarya": "01",
#         "fevralya": "02",
#         "marta": "03",
#         "aprelya": "04",
#         "maya": "05",
#         "iyunya": "06",
#         "iyulya": "07",
#         "avgusta": "08",
#         "sentyabrya": "09",
#         "oktyabrya": "10",
#         "noyabrya": "11",
#         "dekabrya": "12",
#     }

#     if match:
#         day, month_str = match.groups()
#         month_num = MONTHS_RU.get(month_str)
#         year = datetime.now().strftime("%y")
#         if month_num:
#             return f"{int(day):02d}.{month_num}.{year}"
#         else:
#             logger.debug(f"Unknown month: {month_str}")
#     else:
#         logger.debug(f"No date-like string found in file name: {file_name}")
#     return None


async def get_changes_date(url: str):
    file_name = url.split("/")[-1]

    async def parse_date(date_str: str) -> str:
        for fmt in ("%d.%m.%Y", "%d.%m.%y"):
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%d.%m.%y")
            except ValueError:
                continue
        raise ValueError(f"Неподдерживаемый формат даты: {date_str}")

    # Пытаемся найти дату в формате dd.mm.yy или dd.mm.yyyy
    date_match = re.search(r"\d{2}\.\d{2}\.(\d{2}|\d{4})", file_name)
    if date_match:
        raw_date = date_match.group(0)
        try:
            # Пробуем распарсить и привести к нужному формату
            return await parse_date(raw_date)
        except ValueError:
            logger.debug(f"Invalid date format found: {raw_date}")
            return None
    else:
        logger.debug(f"Date not found in the file name: {file_name}")
        return None


async def get_pdf_url_from_page():
    url = "https://ulstu.ru/education/spo/kei/student/schedule/"

    logger.debug(f"Getting a page with URL: {url}")
    response = await asyncio.to_thread(requests.get, url)
    if response.status_code != 200:
        logger.error(
            f"It was not possible to get a page. Status code: {response.status_code}"
        )
        return None

    soup = BeautifulSoup(response.content, "html.parser")

    scripts = soup.find_all("script", type="application/javascript")
    for script in scripts:
        script_content = script.string
        if script_content and "PDFStart" in script_content:
            match = re.search(r"PDFStart\(['\"]([^'\"]+)['\"]\)", script_content)
            if match:
                pdf_url = match.group(1)
                full_pdf_url = requests.compat.urljoin(url, pdf_url)
                return full_pdf_url

    return None
