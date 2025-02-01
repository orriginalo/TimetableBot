from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

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
      InlineKeyboardButton(text="Нет", callback_data="dont_show_changes"),
    ],
  ],
)