from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

main_keyboard = ReplyKeyboardMarkup(
  keyboard=[
    [KeyboardButton(text="⏭️ След. неделя"), KeyboardButton(text="Текущая неделя ⬅️")],
    [KeyboardButton(text="⏭️ Завтра"), KeyboardButton(text="Сегодня ⬅️")],
    [KeyboardButton(text="📃 Изменения"), KeyboardButton(text="Сменить группу 🔄️")],
    [KeyboardButton(text="❔Расписание другой группы❔")],
  ],
  resize_keyboard=True,
  input_field_placeholder="Что ты хочешь узнать?"
)

ask_changes_keyboard = InlineKeyboardMarkup(
  inline_keyboard=[
    [
      InlineKeyboardButton(text="Да", callback_data="show_changes"),
      InlineKeyboardButton(text="Нет", callback_data="dont-show_changes"),
    ],
  ],
)


async def get_settings_keyboard(user: dict):
  
  def get_emoji_by_bool(var: bool):
    return "✅" if var == True else "❌"
  
  def get_callback_by_bool(var: bool):
    return "enable_" if var == True else "disable_"
  
  user_settings = user["settings"]
  
  send_timetable_new_week = user_settings["send_timetable_new_week"]
  send_timetable_updated = user_settings["send_timetable_updated"]
  send_changes_updated = user_settings["send_changes_updated"]
  
  settings_postfix = "_setting"
  
  buttons = {
    "send_timetable_new_week": {
      "text": f"{get_emoji_by_bool(send_timetable_new_week)} Расписание с новой недели",
      "callback": f"{get_callback_by_bool(send_timetable_new_week)}send_timetable_new_week{settings_postfix}"
    },
    # "send_timetable_updated": {
    #   "text": f"{get_emoji_by_bool(send_timetable_updated)} Обновление в расписании",
    #   "callback": f"{get_callback_by_bool(send_timetable_updated)}send_timetable_updated{settings_postfix}"
    # },
    "send_changes_updated": {
      "text": f"{get_emoji_by_bool(send_changes_updated)} Новые изменения",
      "callback": f"{get_callback_by_bool(send_changes_updated)}send_changes_updated{settings_postfix}"
    }
  }
  
  kb = InlineKeyboardBuilder()
  
  for key, value in buttons.items():
    kb.add(InlineKeyboardButton(text=value["text"], callback_data=value["callback"]))
  
  kb.add(InlineKeyboardButton(text="◀️ Назад", callback_data="back"))
  return kb.adjust(1).as_markup()