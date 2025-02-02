# selenium_driver.py
import re
from utils.log import logger
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException
# from webdriver_manager.chrome import ChromeDriverManager
import time
import os
from dotenv import load_dotenv
import variables as var  # если функции calculate_current_study_number_week() и get_monday_of_week() лежат тут

load_dotenv()

class Driver:
    def __init__(self, headless=True, remote=False):
        logger.info("Driver starting...")

        browser_options = None

        if remote:
            browser_options = webdriver.FirefoxOptions()
        else:
            browser_options = webdriver.ChromeOptions()

        if headless:
            browser_options.add_argument("--headless")
        browser_options.add_argument("--disable-gpu")
        browser_options.add_argument("--window-size=1920,1600")
        browser_options.add_argument("--no-sandbox")
        browser_options.add_argument("--disable-dev-shm-usage")

        self._driver = None
        if remote:
            self._driver = webdriver.Remote("http://selenium:4444/wd/hub", options=browser_options)
        else:
            self._driver = webdriver.Chrome(options=browser_options)
        self._wait = WebDriverWait(self._driver, 10)

    @property
    def driver(self):
        return self._driver

    def __getattr__(self, name):
        return getattr(self._driver, name)

    def auth(self, login: str, password: str) -> bool:
        logger.info("Driver authenticating...")
        try:
            self.driver.get("https://lk.ulstu.ru/?q=auth/login")

            login_field = self._wait.until(
                EC.presence_of_element_located((By.NAME, "login"))
            )
            logger.debug(f"Login field found")
            password_field = self.driver.find_element(By.NAME, "password")
            logger.debug(f"Password field found")

            login_field.send_keys(login)
            password_field.send_keys(password)
            password_field.send_keys(Keys.RETURN)
            logger.debug(f"Form with password and login sent")

            self._wait.until(
                lambda d: d.current_url != "https://lk.ulstu.ru/?q=auth/login"
            )
            logger.debug("Driver redirected")

            self._wait.until(
                EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div/div"))
            )
            logger.debug("Profile element will find")
            self.authed = True
            return True

        except Exception as e:
            logger.exception(f"Driver authentication failed: {str(e)}")
            self.authed = False
            return False
        finally:
            time.sleep(1)

    def select_timetable(self, group_name: str, next_week: bool = False):
        """
        Загружает страницу расписания для заданной группы.
        Для текущей недели ищется элемент с классом "week", для следующей – с классом "week-num".
        Также выбирается контейнер с расписанием (элемент с классом "table-responsive") для скриншота.
        Если номер недели не соответствует ожидаемому, возвращается None.
        """
        # Загружаем страницу с расписанием для группы (имя фильтра приводим к нижнему регистру)
        self.driver.get(f"https://time.ulstu.ru/timetable?filter={group_name.lower()}")

        # Ждём появления контейнера с расписанием (находим по наличию класса "table-responsive")
        try:
            timetable_container = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, "//div[contains(@class, 'table-responsive')]/.."))
            )
        except TimeoutException:
            logger.error(f"Контейнер с расписанием не найден для группы {group_name} за 10 секунд.")
            return None

        # Правильный поиск номера недели (не берём "Сейчас X-я неделя", а всегда берём число из расписания)
        week_element = None
        try:
            week_element = WebDriverWait(self.driver, 5).until(
                EC.visibility_of_element_located((By.XPATH, "//div[contains(@class, 'week-num')]"))
            )
            self.driver.execute_script(f"""
                                       let part = arguments[0].innerHTML;
                                       arguments[0].innerHTML += '. {group_name.capitalize()}';
                                       """, week_element)
        except TimeoutException:
            logger.debug("Элемент 'week-num' не найден, ищем в 'week'.")

        week_text = ""
        if week_element:
            week_text = week_element.text.strip()
        else:
            try:
                week_element = WebDriverWait(self.driver, 5).until(
                    EC.visibility_of_element_located((By.XPATH, "//div[@class='week']/div"))
                )
                week_text = week_element.text.strip()
            except TimeoutException:
                logger.error(f"Не найден элемент с номером недели для группы {group_name}.")
                return None

        # Убираем лишний текст, если он есть
        week_text = re.sub(r"Сейчас\s+", "", week_text).strip()

        logger.debug(f"Найден текст недели: '{week_text}'")

        match = re.search(r'(\d+)', week_text)
        if not match:
            logger.error("Не удалось извлечь номер недели: " + week_text)
            return None
        displayed_week = int(match.group(1))
        logger.debug(f"Обнаружен номер недели: {displayed_week}")

        # Вычисляем ожидаемый номер недели:
        # Для текущей недели ожидаем результат функции calculate_current_study_number_week()
        # Для следующей – прибавляем 1
        current_week = var.calculate_current_study_number_week()
        expected_week = current_week + (1 if next_week else 0)
        if displayed_week != expected_week:
            logger.error(f"Ожидалась неделя {expected_week}, а отображается неделя {displayed_week} для группы {group_name}.")
            return None
        logger.debug(f"Номер недели {displayed_week} соответствует ожидаемому.")

        # Удаляем ненужные элементы: навигационную панель, панель поиска, блоки с неделей
        self.driver.execute_script("""
            document.querySelector('nav.navbar')?.remove();
            document.querySelector('.layout-panel')?.remove();
            document.querySelector('.input-group')?.remove();
            document.querySelector('.week')?.remove();
        """)
            # document.querySelector('.week-num')?.remove();
        header_cols = WebDriverWait(driver, 10).until(
            EC.visibility_of_all_elements_located((By.XPATH, "//div[@class='table-header-col']/div"))
        )

        for col in header_cols:
            if any(weekday in col.text for weekday in ["Пнд", "Втр", "Срд", "Чтв", "Птн", "Сбт", "Вск"]):
                # Удаляем всё после переноса строки (включая дату)
                self.driver.execute_script("""
                    let parts = arguments[0].innerHTML.split('<br>');
                    arguments[0].innerHTML = parts[0].trim();
                """, col)

        # Прокручиваем страницу так, чтобы контейнер был виден
        self.driver.execute_script("arguments[0].scrollIntoView(true);", timetable_container)
        self.driver.execute_script("window.scrollBy(0, 50);")

        return timetable_container



    def quit(self):
        """Закрыть браузер и завершить сессию"""
        if self._driver:
            self._driver.quit()

driver = Driver(headless=True, remote=False)
