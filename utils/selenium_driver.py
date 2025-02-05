import re
import asyncio
import os
from dotenv import load_dotenv
from utils.log import logger
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import variables as var

load_dotenv()

class AsyncDriver:
    def __init__(self, headless=True, remote=False, n=None):
        if n is None:
            logger.info("Driver starting...")
        else:
            logger.info(f"Driver {n} starting...")
                   
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1600")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        self._driver = None
        if remote:
            self._driver = webdriver.Remote("http://selenium:4444/wd/hub", options=options)
        else:
            self._driver = webdriver.Chrome(options=options)
        
        self._wait = WebDriverWait(self._driver, 10)
        self.authed = False
    
    @property
    def driver(self):
        return self._driver

    def __getattr__(self, name):
        return getattr(self._driver, name)

    async def auth(self, login: str, password: str) -> bool:
        logger.info("Driver authenticating...")
        try:
            await asyncio.to_thread(self.driver.get, "https://lk.ulstu.ru/?q=auth/login")
            
            login_field = await asyncio.to_thread(
                lambda: self._wait.until(EC.presence_of_element_located((By.NAME, "login")))
            )
            logger.debug("Login field found")
            
            password_field = self.driver.find_element(By.NAME, "password")
            logger.debug("Password field found")
            
            await asyncio.to_thread(login_field.send_keys, login)
            await asyncio.to_thread(password_field.send_keys, password)
            await asyncio.to_thread(password_field.send_keys, Keys.RETURN)
            logger.debug("Form submitted")

            await asyncio.to_thread(
                lambda: self._wait.until(lambda d: d.current_url != "https://lk.ulstu.ru/?q=auth/login")
            )
            logger.debug("Driver redirected")

            await asyncio.to_thread(
                lambda: self._wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div/div")))
            )
            logger.debug("Profile element found")

            self.authed = True
            return True
        except Exception as e:
            logger.exception(f"Driver authentication failed: {str(e)}")
            self.authed = False
            return False
        finally:
            await asyncio.sleep(1)

    async def select_timetable(self, group_name: str, next_week: bool = False):
        await asyncio.to_thread(self.driver.get, f"https://time.ulstu.ru/timetable?filter={group_name.lower()}")

        try:
            timetable_containers = await asyncio.to_thread(
                lambda: WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_all_elements_located((By.CLASS_NAME, "table-responsive"))
                )
            )
            timetable_containers = [container.find_element(By.XPATH, "..") for container in timetable_containers]
            
            for container in timetable_containers:
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].style.padding = '12px 12px 12px 12px';", container)

                week_element = None
                try:
                    week_element = container.find_element(By.CLASS_NAME, "week-num")
                except NoSuchElementException:
                    logger.debug("Элемент 'week-num' не найден, ищем в 'week'.")
                
                week_text = ""
                if week_element:
                    week_text = week_element.text.strip()
                else:
                    try:
                        week_element = container.find_element(By.XPATH, "//div[@class='week']/div")
                        week_text = week_element.text.strip()
                    except NoSuchElementException:
                        logger.error(f"Не найден элемент с номером недели в контейнере.")
                        continue  # Пропускаем этот контейнер и проверяем следующий
                
                week_text = re.sub(r"Сейчас\s+", "", week_text).strip()
                logger.debug(f"Найден текст недели: '{week_text}'")
                
                match = re.search(r'(\d+)', week_text)
                if not match:
                    logger.error(f"Не удалось извлечь номер недели: {week_text}")
                    continue
                
                displayed_week = int(match.group(1))
                logger.debug(f"Обнаружен номер недели: {displayed_week}")
                
                current_week = var.calculate_current_study_number_week()
                expected_week = current_week + (1 if next_week else 0)

                if displayed_week == expected_week:
                    logger.debug(f"Найден подходящий контейнер с неделей {displayed_week}.")
                    
                    # Удаляем ненужные контейнеры
                    for other_container in timetable_containers:
                        if other_container != container:
                            self.driver.execute_script("arguments[0].parentNode.removeChild(arguments[0]);", other_container)
                    
                    return container
            
            logger.error(f"Не найден контейнер с неделей {expected_week} для группы {group_name}.")
            return None

        except TimeoutException:
            logger.error(f"Контейнеры с расписанием не найдены для группы {group_name} за 10 секунд.")
            return None


    async def quit(self):
        if self._driver:
            await asyncio.to_thread(self._driver.quit)


class AsyncDriverPool:
    """
    Пул драйверов для переиспользования экземпляров AsyncDriver.
    """
    def __init__(self, pool_size=5, headless=True, remote=False):
        self.pool_size = pool_size
        self.headless = headless
        self.remote = remote
        self.pool = asyncio.Queue(maxsize=pool_size)
        self.login = os.getenv("LOGIN")
        self.password = os.getenv("PASSWORD")

    async def reauth(self):
        logger.info("Reauthing drivers...")
        drivers_to_reauth = []
        # Забираем все драйверы из пула (фиксируем текущий размер)
        current_pool_size = self.pool.qsize()
        for _ in range(current_pool_size):
            driver = await self.pool.get()
            # Если драйвер занят, ждём, пока он освободится
            drivers_to_reauth.append(driver)
        
        # Переаутентифицируем все драйверы (которые теперь свободны)
        tasks = [self._reauth_driver(driver) for driver in drivers_to_reauth]
        await asyncio.gather(*tasks)

    async def _reauth_driver(self, driver: 'AsyncDriver'):
        logger.info(f"Reauthenticating driver #{driver.n}...")
        success = await driver.auth(self.login, self.password)
        if success:
            logger.info(f"Driver #{driver.n} reauthenticated successfully.")
        else:
            logger.error(f"Reauthentication failed for driver #{driver.n}.")
        # Возвращаем драйвер обратно в пул
        await self.pool.put(driver)

    async def init_pool(self):
        for i in range(self.pool_size):
            driver = AsyncDriver(headless=self.headless, remote=self.remote, n=i+1)
            # Если требуется аутентификация для каждого драйвера, выполняем её здесь:
            await driver.auth(self.login, self.password)
            await self.pool.put(driver)
        logger.info(f"Пул из {self.pool_size} драйверов успешно создан.")

    async def acquire(self) -> AsyncDriver:
        driver = await self.pool.get()
        return driver

    async def release(self, driver: AsyncDriver):
        await self.pool.put(driver)

    async def close_all(self):
        while not self.pool.empty():
            driver = await self.pool.get()
            await driver.quit()
        logger.info("Все драйверы из пула закрыты.")


# Глобальная переменная для пула
driver_pool: AsyncDriverPool = None

async def init_driver_pool():
    global driver_pool
    driver_pool = AsyncDriverPool(pool_size=5, headless=True, remote=False, login=os.getenv("LOGIN"), password=os.getenv("PASSWORD"))
    await driver_pool.init_pool()


async def handle_request(group_name: str, next_week: bool):
    driver = await driver_pool.acquire()
    try:
        timetable = await driver.select_timetable(group_name, next_week)
        return timetable
    finally:
        await driver_pool.release(driver)


# Инициализация пула драйверов при запуске приложения
# Глобальная переменная для пула
driver_pool = None

# Инициализация пула при импорте модуля
async def _init_driver_pool():
    global driver_pool
    pool_size = 3
    try:
        pool_size = int(os.getenv("DRIVER_POOL_SIZE"))
    except ValueError:
        logger.warning("DRIVER_POOL_SIZE is not an integer, defaulting to 3")
    except Exception as e:
        logger.error(f"Error parsing DRIVER_POOL_SIZE from .env: {e}")
    driver_pool = AsyncDriverPool(pool_size=pool_size, headless=True, remote=False)
    await driver_pool.init_pool()

# Автоматическая инициализация пула
loop = asyncio.get_event_loop()
loop.run_until_complete(_init_driver_pool())