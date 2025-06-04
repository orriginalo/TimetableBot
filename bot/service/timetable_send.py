from aiogram.types import FSInputFile
from bot.database.models import User
from bot.database.queries.user import get_users
from bot.requests.screenshots import get_screenshot_path
from utils.log import logger
from aiogram import Bot

async def send_new_timetable(bot: Bot):
    logger.info("Sending timetable to next week...")

    users_with_notifications = await get_users(
        User.settings["send_timetable_new_week"].as_boolean() == True  # noqa: E712
    )

    for user in users_with_notifications:
        group_name = user.group_name
        logger.debug(
            f"Started screening timetable for group {group_name} (текущая неделя)..."
        )
        screenshot_path = await get_screenshot_path(group_name, "nextweek")

        try:
            photo = FSInputFile(screenshot_path)
            await bot.send_photo(
                user.tg_id,
                photo=photo,
                caption="🔔 Расписание на следующую неделю",
                parse_mode="html",
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке скриншота: {e}")

        return screenshot_path
