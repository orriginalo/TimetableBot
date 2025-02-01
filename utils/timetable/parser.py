from utils.log import logger
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import json
import os
from variables import prefixes_map, subjects_map, postfixes
START_STUDY_WEEK_NUM = 34 # Неделя с которой началась учеба в 2024 году

ADDED_WEEKS = 20 # В переходе на 2 семестр 2024/2025 срезали 20 недель (теперь над расписанием пишется неделя начиная с 1)

def process_subject_name(subject: str, subjects_map: dict, prefixes_map: dict = None) -> str:

    """
    Обрабатывает название предмета, заменяя префиксы и длинные названия.

    Args:
        subject (str): Название предмета из расписания.
        subjects_map (dict): Словарь с заменами названий предметов.
        prefixes_map (dict, optional): Словарь с заменами префиксов.

    Returns:
        str: Обработанное название.
    """
    if subject == "-":
        return subject
    
    if subject.startswith("Лаб.Информатика"):
        subject = subject.replace("Лаб.Информатика", "Информатика")
        
    prefix: str = None
    subject_name: str = subject
    postfix: str = None

    for pr, _ in prefixes_map.items():
        if pr in subject.lower():
            prefix = subject_name[:len(pr)]
            break

    for pf in postfixes:
        if pf in subject:
            postfix = pf
            break
        else:
            postfix = ""

    if prefix:
        subject_name = subject_name.replace(prefix, "")

    if postfix:
        subject_name = subject_name.replace(postfix, "")

    processed_prefix: str = prefixes_map.get(prefix.lower(), prefix) if (prefixes_map is not None and prefix is not None) else ""
    processed_subject_name: str = subjects_map.get(subject_name.lower(), subject_name) if (subjects_map is not None) else ""

    if processed_prefix is not None:
        if processed_prefix.endswith("."):
            processed_prefix += " "

    processed_prefix = "" if prefix is None else processed_prefix
    postfix = "" if postfix is None else postfix

    processed_subject = f"{processed_prefix}{processed_subject_name}{postfix}"

    return processed_subject

def get_monday_timestamp(week_number: int, year: int) -> int:
    """
    Возвращает округленный timestamp понедельника указанной недели, учитывая переход на следующий год.

    :param week_number: Номер недели (1 и выше).
    :param year: Год, с которого начинается расчет.
    :return: Округленный до целого timestamp понедельника.
    """
    # Определяем первый день года
    first_day_of_year = datetime(year, 1, 1)
    
    # Определяем смещение до первого понедельника года
    days_to_monday = (7 - first_day_of_year.weekday()) % 7
    first_monday = first_day_of_year + timedelta(days=days_to_monday)
    
    # Вычисляем целевой понедельник
    target_monday = first_monday + timedelta(weeks=week_number - 1)
    
    # Если целевой понедельник относится к следующему году, обновляем year
    if target_monday.year > year:
        year = target_monday.year
    
    return round(target_monday.timestamp())

def get_iterable_text(soup_find_text):
  return [text.strip() for text in soup_find_text.splitlines() if text.strip()] if len(soup_find_text) > 2 else []

def parse_timetable(html_file: str, json_file: str = None, add_groupname_to_json: bool = False, group_name: str = None):

    timetable = {}
    if json_file is not None:
        if not os.path.exists(json_file):
            with open(json_file, "w", encoding="utf-8") as file:
                file.write("{}")
        timetable = json.load(open(json_file, "r", encoding="utf-8")) # Загружаем расписание из json файла

    def clean_text(text):
        """Очистка текста от лишних символов."""
        return " ".join(text.split()).strip()

    try:
        with open(html_file, "r", encoding="utf-8") as file:
            soup = BeautifulSoup(file, "html.parser")
    except:
        logger.exception(f"Error parsing {html_file}")
        return {}
    # Ищем все недели
    week_sections = soup.find_all("div", class_="week-num")
    
    for week_section in week_sections:
        re_week_name = re.findall(r'\d+', clean_text(week_section.text))
        week_num = re_week_name[0]
        week_num_real = int(week_num) + ADDED_WEEKS - 1 #
        week_num_real = str(week_num_real)
        if add_groupname_to_json:
            timetable[group_name] = {}
            timetable[group_name][week_num_real] = {}
        else:
            timetable[week_num_real] = {}
        
        # Секция соответствующих дней недели
        week_container = week_section.find_next("div", class_="container")
        day_rows = week_container.find_all("div", class_="row")
        
        try:
            day_rows.pop(0)
        except:
            return {}

        first_day_of_the_week = get_monday_timestamp(int(week_num) + START_STUDY_WEEK_NUM + ADDED_WEEKS, 2024)
        for day_row in day_rows:
            day_col = day_row.find("div", class_="table-header-col")
            if not day_col:
                continue  # Пропуск строки, если это не день
            
            # date = datetime.fromtimestamp(first_day_of_the_week).strftime("%d/%m/%Y, %H:%M:%S")
            date = first_day_of_the_week
            date = str(date)
            if add_groupname_to_json:
                timetable[group_name][week_num_real][date] = {}
            else:
                timetable[week_num_real][date] = {}

            first_day_of_the_week += 86400
            
            # Колонки пар
            pair_cols = day_row.find_all("div", class_="table-col")
            for pair_index, pair_col in enumerate(pair_cols, start=1):
                pair_label = f"{pair_index}"
                cell_text_it: list = get_iterable_text(pair_col.text)

                subject = "-"
                if len(cell_text_it) >= 3:
                    subject = cell_text_it[2]


                # Заменяем длинные названия на более короткие
                # if replace_subject_to_short:
                #     subject = short_subjects.get(subject.replace("пр.", "").lower(), subject)

                # if do_process_prefixes:
                #     subject = process_subject_name(subject)

                subject = process_subject_name(subject, subjects_map=subjects_map, prefixes_map=prefixes_map)

                if add_groupname_to_json:
                    timetable[group_name][week_num_real][date][pair_label] = subject
                else:
                    timetable[week_num_real][date][pair_label] = subject
    
    if json_file is not None:
        with open(json_file, "w", encoding="utf-8") as file:
            json.dump(timetable, file, ensure_ascii=False, indent=4)
        logger.info(f"Timetable {group_name} saved to {json_file}")

    return timetable