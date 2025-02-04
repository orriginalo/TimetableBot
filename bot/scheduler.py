from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from utils.timetable.sender import send_new_timetable
from utils.changes import check_changes_job
from utils.log import logger
from variables import update_cache_duration
from utils.selenium_driver import driver_pool

scheduler = AsyncIOScheduler()

async def start_scheduler(bot: Bot):
    try:
        await check_changes_job(bot)
        await update_cache_duration()
        # await driver_pool.reauth()
        scheduler.add_job(driver_pool.reauth, 'interval', hours=2, max_instances=1)
        scheduler.add_job(update_cache_duration, CronTrigger(minute=00, second=00))
        scheduler.add_job(check_changes_job, 'interval', minutes=3, args=[bot])
        scheduler.add_job(send_new_timetable, CronTrigger(day_of_week="sun", hour=14, minute=00), args=[bot])
        scheduler.start()
    except Exception as e:
        logger.exception(f"Error starting scheduler: {e}")