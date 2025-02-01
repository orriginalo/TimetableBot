from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

main_keyboard = ReplyKeyboardMarkup(
  keyboard=[
    [KeyboardButton(text="⏭️ След. неделя"), KeyboardButton(text="Текущая неделя ⬅️")],
    [KeyboardButton(text="⏭️ Завтра"), KeyboardButton(text="Сегодня ⬅️")],
    [KeyboardButton(text="📃 Изменения"), KeyboardButton(text="Настройки 🔧")],
    [KeyboardButton(text="❔Расписание другой группы❔")],
  ],
  resize_keyboard=True,
  input_field_placeholder="Что ты хочешь узнать?"
)