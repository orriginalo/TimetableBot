import logging
import datetime
from bot.config import settings
import os

def setup_logger() -> logging.Logger:
    try:
        log_level = getattr(logging, settings.LOG_LEVEL)
    except AttributeError:
        print(settings.LOG_LEVEL)
        print("Log level not found (check LOG_LEVEL in .env), defaulting to INFO")
        log_level = logging.INFO

    # Убедимся, что папка для логов существует
    log_dir = "data/logs"
    os.makedirs(log_dir, exist_ok=True)

    # Создаём имя файла для логов на основе текущей даты
    log_filename = os.path.join(
        log_dir, f"{datetime.datetime.now().strftime('%Y-%m-%d')}.log"
    )

    # Создаём главный логгер
    logger = logging.getLogger("TimetableBot")
    logger.setLevel(log_level)

    # Проверяем, чтобы обработчики не дублировались
    if not logger.hasHandlers():
        # Настраиваем обработчик для записи в файл
        file_handler = logging.FileHandler(log_filename, encoding="utf-8")
        file_handler.setLevel(log_level)
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%d.%m.%Y %H:%M:%S",
            )
        )

        # Настраиваем обработчик для вывода в консоль
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))

        # Добавляем обработчики в логгер
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger


# Получение настроенного логгера
logger = setup_logger()
