from datetime import datetime, timedelta

default_user_settings: dict = {
  "send_timetable_new_week": False,
  "send_timetable_updated": False,
  "send_changes_updated": False,
}



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
