import asyncio
from utils.log import logger
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image

from rich import print
import json
from dotenv import load_dotenv
import os

load_dotenv()

login = os.getenv("LOGIN")
password = os.getenv("PASSWORD")


from selenium.common.exceptions import TimeoutException

def download_timetable(driver, groups: list[str], make_screenshot: bool = False):
    logger.debug(f"Started downloading timetable for groups: {groups}...")
    try:
        for group in groups:
            driver.get(f"https://time.ulstu.ru/timetable?filter={group.lower()}")
            parent_container = None
            try:
                # Wait for the parent container to be visible
                parent_container = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located(
                        (By.XPATH, "/html/body/div/div/div/div[2]/div/div[3]")
                    )
                )
            except TimeoutException:
                logger.error(f"Parent container not found for group {group} within 10 seconds.")
                continue  # Skip to next group if element not found

            page_html = driver.page_source

            if make_screenshot:
                if not parent_container:
                    logger.error(f"Cannot take screenshot for {group}: parent container missing.")
                    continue

                # Remove unwanted elements
                driver.execute_script("""
                    document.querySelector('nav.navbar')?.remove();
                    document.querySelector('.layout-panel')?.remove();
                    document.querySelector('.input-group')?.remove();
                    document.querySelector('.week')?.remove();
                    const weekNums = document.querySelectorAll('.week-num');
                    if (weekNums.length > 1) weekNums[0].parentElement.remove();
                """)

                # Scroll to the container and take screenshot
                driver.execute_script("arguments[0].scrollIntoView(true);", parent_container)
                driver.execute_script("window.scrollBy(0, 50);")
                screenshot_path = f"./data/screenshots/{group.lower()}.png"
                driver.save_screenshot(screenshot_path)

                # Define crop area with margins
                margin = 35
                rect = parent_container.rect
                crop_box = (
                    max(0, int(rect['x']) - margin),
                    max(0, int(rect['y']) - margin),
                    int(rect['x'] + rect['width'] + margin),
                    int(rect['y'] + rect['height'] + margin)
                )

                # Crop and save the image
                image = Image.open(screenshot_path)
                cropped_image = image.crop(crop_box)
                cropped_image.save(screenshot_path)
                logger.debug(f"Screenshot saved: {screenshot_path}")

            # Save HTML
            html_path = f"./data/timetables/html/{group.lower()}-timetable.html"
            with open(html_path, "w", encoding="utf-8") as file:
                file.write(page_html)
            logger.debug(f"HTML saved: {html_path}")

    except Exception as e:
        logger.exception(f"Error processing group {group}: {e}")
