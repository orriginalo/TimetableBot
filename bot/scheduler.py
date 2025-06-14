from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from bot.service.timetable_send import send_new_timetable
from bot.service.changes import check_changes_job
from utils.log import logger

scheduler = AsyncIOScheduler()


async def start_scheduler(bot: Bot):
    try:
        await check_changes_job(bot)
        scheduler.add_job(check_changes_job, "interval", minutes=3, args=[bot])
        scheduler.add_job(
            send_new_timetable,
            CronTrigger(day_of_week="sun", hour=14, minute=00),
            args=[bot],
        )
        scheduler.start()
    except Exception as e:
        logger.exception(f"Error starting scheduler: {e}")
