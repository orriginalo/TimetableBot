from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

main_keyboard = ReplyKeyboardMarkup(
  keyboard=[
    [KeyboardButton(text="⏭️ След. неделя"), KeyboardButton(text="Текущая неделя ⬅️")],
    [KeyboardButton(text="⏭️ Завтра"), KeyboardButton(text="Сегодня ⬅️")],
    [KeyboardButton(text="📋 Изменения"), KeyboardButton(text="Настройки 🔧")],
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

other_group_when = InlineKeyboardMarkup(
  inline_keyboard=[
    [InlineKeyboardButton(text="⏭️ Следующая", callback_data="next-week_other_group"), InlineKeyboardButton(text="Текущая ⬅️", callback_data="current-week_other_group")],
  ]
)

empty_inline = InlineKeyboardMarkup(inline_keyboard=[])

async def get_settings_keyboard(user: dict):
  def get_emoji_by_bool(var: bool):
    return "✅" if var else "❌"

  def get_callback_by_bool(var: bool):
    return "enable_" if var else "disable_"

  settings_postfix = "_setting"

  settings = [
    {"key": "send_timetable_new_week", "label": "Расписание с новой недели"},
    {"key": "send_changes_updated", "label": "Новые изменения"},
    {"key": "send_changes_when_isnt_group", "label": "Изменения когда группы нет"}
  ]

  kb = InlineKeyboardBuilder()

  kb.add(InlineKeyboardButton(text="🔄️ Сменить группу", callback_data="change-group"))

  for setting in settings:
    key = setting["key"]
    label = setting["label"]
    value = user["settings"].get(key, False)  # По умолчанию False, если нет ключа
    kb.add(InlineKeyboardButton(
      text=f"{get_emoji_by_bool(value)} {label}",
      callback_data=f"{get_callback_by_bool(value)}{key}{settings_postfix}"
    ))

  kb.add(InlineKeyboardButton(text="« Назад", callback_data="back-settings"))
  return kb.adjust(1).as_markup()
