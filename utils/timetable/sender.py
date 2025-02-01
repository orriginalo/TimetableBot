from aiogram.types import FSInputFile
from bot.database.models import User
from bot.database.queries.group import get_group_by_id
from bot.database.queries.user import get_users
from utils.log import logger
from utils.timetable.downloader import download_timetable
from utils.selenium_driver import driver

async def send_new_timetable(bot):
    logger.info("Sending timetable to next week...")

    users_with_notifications = await get_users(User.settings['send_timetable_new_week'].as_boolean() == True)
    groups: set = set()
    for user in users_with_notifications:
      groups.add((await get_group_by_id(user['group_id']))["name"])

    groups = list(groups)
    download_timetable(driver=driver, groups=groups, make_screenshot=True)
    for user in users_with_notifications:
        photo = FSInputFile(f"./data/screenshots/{user["group_name"]}.png")
        await bot.send_photo(user["tg_id"], photo, caption="🔔 Расписание на следующую неделю")