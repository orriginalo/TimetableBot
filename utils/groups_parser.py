from bs4 import BeautifulSoup
from bot.database.queries.group import add_group, delete_all_groups
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import os
from dotenv import load_dotenv

load_dotenv()

# Логин и пароль из .env
login = os.getenv("LOGIN")
password = os.getenv("PASSWORD")


async def parse_groups_and_add_to_db(driver):
    driver.get("https://time.ulstu.ru/groups")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, "/html/body/div/div/div/div[2]/div/div[2]")
        )
    )
    soup = BeautifulSoup(driver.page_source, "lxml")
    groups_container = soup.find("div", class_="container-fluid")
    groups_list = [
        group.strip() for group in groups_container.text.split("\n") if group.strip()
    ]

    driver.get("https://time.ulstu.ru/teachers")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, "/html/body/div/div/div/div[2]/div/div[2]/div[1]")
        )
    )
    soup = BeautifulSoup(driver.page_source, "lxml")
    teachers_container = soup.find("div", class_="container-fluid")
    teachers_list = [
        teacher.strip()
        for teacher in teachers_container.text.split("\n")
        if teacher.strip()
    ]
    print(teachers_container.text.split("\n"))
    print(teachers_list)
    total_list = groups_list + teachers_list

    await delete_all_groups()
    for group in total_list:
        try:
            await add_group(group)
        except Exception as e:
            print("Error adding group: ", group, "| Error: ", e)

    return groups_list
