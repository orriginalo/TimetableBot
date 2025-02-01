from datetime import datetime, timedelta

default_user_settings: dict = {
  "send_timetable_new_week": False,
  "send_timetable_updated": False,
  "send_changes_updated": False,
}

CURRENT_WEEK_CORRECTION: int = -2

def get_monday_of_week(week_number: int, year: int = None) -> datetime:
    if year is None:
        year = datetime.now().year
        
    first_thursday = datetime(year, 1, 4)
    first_monday = first_thursday - timedelta(days=first_thursday.weekday())
    return first_monday + timedelta(weeks=week_number - 1)

def calculate_current_study_number_week():
  current_week = datetime.now().isocalendar()[1]
  return current_week + CURRENT_WEEK_CORRECTION

print(calculate_current_study_number_week())

def calculate_yesterday():
  """
  [0] - midnight datetime
  [1] - timestamp
  """
  yesterday_midnight = (datetime.now() - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
  yesterday_ts = int(yesterday_midnight.timestamp())

  return [yesterday_midnight, yesterday_ts]

def calculate_today():
  """
  [0] - midnight datetime
  [1] - timestamp
  """
  today_midnight = (datetime.now()).replace(hour=0,minute=0,second=0,microsecond=0)
  today_ts = int(today_midnight.timestamp())

  return [today_midnight, today_ts]


def calculate_tomorrow():
  """
  [0] - midnight datetime
  [1] - timestamp
  """
  tomorrow_midnight = (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
  tomorrow_ts = int(tomorrow_midnight.timestamp())

  return [tomorrow_midnight, tomorrow_ts]

def calculate_aftertomorrow():
  """
  [0] - midnight datetime
  [1] - timestamp
  """
  after_tomorrow_midnight = (datetime.now() + timedelta(days=2)).replace(hour=0, minute=0, second=0, microsecond=0)
  after_tomorrow_ts = int(after_tomorrow_midnight.timestamp())

  return [after_tomorrow_midnight, after_tomorrow_ts]
