from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from bot.database.queries.user import update_user, get_user_by_id
from bot.database.queries.group import get_all_groups, get_group_by_name

import bot.keyboards as kb
from utils.changes import instantly_send_changes

class SetGroup(StatesGroup):
  group_name = State()
  
class SeeOtherTimetable(StatesGroup):
  group_name = State()

router = Router()


@router.message(CommandStart())
async def _(msg: Message, state: FSMContext):
  await msg.answer("👋 Введи название группы (например: <code>вдо-12</code>, <code>исдо-25</code>)", parse_mode="html", reply_markup=ReplyKeyboardRemove())
  await state.set_state(SetGroup.group_name)
  
@router.message(SetGroup.group_name)
async def _(msg: Message, state: FSMContext):
  group_name = msg.text.strip().lower()
  if await get_group_by_name(group_name):
    await msg.answer("Группа задана.", reply_markup=kb.main_keyboard)
    await update_user(msg.from_user.id, group_name=group_name)
    await state.clear()
  else:
    await msg.answer("Группа не найдена. Попробуй еще раз.")
    
@router.message(F.text == "⏭️ След. неделя")
async def _(msg: Message):
  pass

@router.message(F.text == "Текущая неделя ⬅️")
async def _(msg: Message):
  pass

@router.message(F.text == "⏭️ Завтра")
async def _(msg: Message):
  pass

@router.message(F.text == "Сегодня ⬅️")
async def _(msg: Message):
  pass

@router.message(F.text == "📃 Изменения")
async def _(msg: Message):
  print("Handling changes")
  await instantly_send_changes(msg.bot, await get_user_by_id(msg.from_user.id))

@router.message(F.text == "Сменить группу 🔄️")
async def _(msg: Message):
  pass

@router.message(F.text == "❔Расписание другой группы❔")
async def _(msg: Message):
  pass

@router.message(Command("settings"))
async def show_settings(message: Message, state: FSMContext):
  await state.clear()
  user = await get_user_by_id(message.from_user.id)
  await message.answer("🔧 Настройки рассылки:", reply_markup=await kb.get_settings_keyboard(user))
    
# User settings: {"send_timetable_new_week": false, "send_timetable_updated": false, "send_changes_updated": false}

@router.callback_query(F.data.contains("setting"))
async def settings_handler(call: CallbackQuery):
  setting_name = call.data.replace("_setting", "").replace("disable_", "").replace("enable_", "")
  setting_condition = False if call.data.split("_")[0] == "disable" else True
  print(setting_name, setting_condition)
  user = await get_user_by_id(call.from_user.id)
  user_settings = user["settings"]
  user_settings_copy = user_settings.copy()
  match (setting_name):
    case "send_timetable_new_week":
      user_settings_copy["send_timetable_new_week"] = not setting_condition
    case "send_timetable_updated":
      user_settings_copy["send_timetable_updated"] = not setting_condition
    case "send_changes_updated":
      user_settings_copy["send_changes_updated"] = not setting_condition
    case _:
      pass
  user = await update_user(call.from_user.id, settings=user_settings_copy)
  updated_kb = await kb.get_settings_keyboard(user)
  await call.message.edit_reply_markup(reply_markup=updated_kb)

@router.callback_query(F.data.contains("_changes"))
async def _(callback: CallbackQuery):
  condition = callback.data.split("_")[0]
  # Checking changes logic
  
  # 
  changes_date = "placeholder"
  match condition:
    case "show":
      await callback.message.delete()
      await callback.message.answer(f"Изменения на <b>{changes_date}</b>", reply_markup=kb.ask_changes_keyboard)
    case "dont_show":
      await callback.message.delete()
      