import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from bot.database.queries.user import update_user, get_user_by_id, get_users
from bot.database.queries.group import get_group_by_name

import bot.keyboards as kb
from bot.service.changes import instantly_send_changes
from bot.requests.screenshots import fetch_screenshot_path_and_send


class SetGroup(StatesGroup):
    group_name = State()


class SeeOtherTimetable(StatesGroup):
    last_bot_msg = State()
    group_name = State()


class ShowChanges(StatesGroup):
    changes_data = State()


class SendToAllAdmin(StatesGroup):
    text = State()


router = Router()


@router.message(CommandStart())
async def _(msg: Message, state: FSMContext):
    await msg.answer(
        "👋 Введи название группы (например: <code>вдо-12</code>, <code>исдо-25</code>)",
        parse_mode="html",
        reply_markup=ReplyKeyboardRemove(),
    )
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
    user = await get_user_by_id(msg.from_user.id)
    await fetch_screenshot_path_and_send(user.group_name, "nextweek", msg)


@router.message(F.text == "Текущая неделя ⬅️")
async def _(msg: Message):
    user = await get_user_by_id(msg.from_user.id)
    await fetch_screenshot_path_and_send(user.group_name, "full", msg)


@router.message(F.text == "⏭️ Завтра")
async def _(msg: Message):
    user = await get_user_by_id(msg.from_user.id)
    await fetch_screenshot_path_and_send(user.group_name, "tomorrow", msg)


@router.message(F.text == "Сегодня ⬅️")
async def _(msg: Message):
    user = await get_user_by_id(msg.from_user.id)
    await fetch_screenshot_path_and_send(user.group_name, "today", msg)


@router.message(F.text == "📋 Изменения")
async def _(msg: Message, state: FSMContext):
    await state.set_state(ShowChanges.changes_data)
    await instantly_send_changes(
        msg, state, await get_user_by_id(msg.from_user.id), with_ask=True
    )


@router.message(F.text.lower().contains("сменить группу"))
async def _(msg: Message, state: FSMContext):
    await msg.answer(
        "✍️ Введи название группы (например: <code>вдо-12</code>, <code>исдо-25</code>)",
        parse_mode="html",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(SetGroup.group_name)


@router.callback_query(F.data == "change-group")
async def _(call: CallbackQuery, state: FSMContext):
    await call.message.answer(
        "✍️ Введи название группы (например: <code>вдо-12</code>, <code>исдо-25</code>)",
        parse_mode="html",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(SetGroup.group_name)


@router.message(F.text == "❔Расписание другой группы❔")
async def _(msg: Message, state: FSMContext):
    user = await get_user_by_id(msg.from_user.id)

    if user.recent_groups and len(user.recent_groups) > 0:
        sent_message = await msg.answer(
            "✍️ Введи название группы",
            parse_mode="html",
            reply_markup=await kb.get_recent_groups_keyboard(user),
        )
        await state.update_data(last_bot_msg=sent_message)
    else:
        await msg.answer(
            "✍️ Введи название группы",
            parse_mode="html",
            reply_markup=await kb.get_recent_groups_keyboard(user),
        )
    await state.set_state(SeeOtherTimetable.group_name)


@router.callback_query(F.data == "back")
async def _(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(text="❌ Действие отменено.")
    try:
        await call.message.edit_reply_markup(reply_markup=kb.empty_inline)
    except Exception as e:
        print(e)
    await state.clear()


@router.callback_query(F.data == "back-settings")
async def _(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(text="✅ Настройки применены.")
    try:
        await call.message.edit_reply_markup(reply_markup=kb.empty_inline)
    except Exception as e:
        print(e)
    await state.clear()


@router.callback_query(
    F.data.startswith("see-other-group_"), SeeOtherTimetable.group_name
)
async def _(call: CallbackQuery, state: FSMContext):
    user = await get_user_by_id(call.from_user.id)
    group_name = call.data.split("_")[1]
    await state.update_data(group_name=group_name)
    await call.message.answer("На какую неделю?", reply_markup=kb.other_group_when)
    recent_groups = user.recent_groups
    recent_groups.remove(group_name)
    await update_user(call.from_user.id, recent_groups=recent_groups + [group_name])
    await call.message.delete()


@router.message(SeeOtherTimetable.group_name)
async def _(msg: Message, state: FSMContext):
    user = await get_user_by_id(msg.from_user.id)
    group_name = msg.text.strip().lower()
    if await get_group_by_name(group_name):
        last_bot_msg: Message = (await state.get_data()).get("last_bot_msg", None)
        if last_bot_msg:
            await last_bot_msg.edit_reply_markup(reply_markup=kb.empty_inline)
        await state.update_data(group_name=group_name)
        await msg.answer("На какую неделю?", reply_markup=kb.other_group_when)
        recent_groups = user.recent_groups
        if recent_groups:
            if group_name not in recent_groups:
                if len(recent_groups) == 2:
                    recent_groups.pop(0)
                await update_user(
                    msg.from_user.id, recent_groups=user.recent_groups + [group_name]
                )
            else:
                recent_groups.remove(group_name)
                await update_user(
                    msg.from_user.id, recent_groups=recent_groups + [group_name]
                )
        else:
            await update_user(msg.from_user.id, recent_groups=[group_name])
    else:
        await msg.answer("Группа не найдена. Попробуй еще раз.")


@router.callback_query(F.data.contains("_other_group"))
async def _(call: CallbackQuery, state: FSMContext):
    group_name = (await state.get_data())["group_name"]
    condition = call.data.split("_")[0]
    await call.message.delete()
    match condition:
        case "next-week":
            await fetch_screenshot_path_and_send(group_name, "nextweek", call.message)
            await state.clear()
        case "current-week":
            await fetch_screenshot_path_and_send(group_name, "full", call.message)
            await state.clear()
        case _:
            await call.answer("🚫 Что-то пошло не так. Попробуй еще раз.")


@router.message(F.text.lower().contains("настройки"))
@router.message(Command("settings"))
async def show_settings(message: Message, state: FSMContext):
    await state.clear()
    user = await get_user_by_id(message.from_user.id)
    await message.answer(
        "🔧 Настройки рассылки:", reply_markup=await kb.get_settings_keyboard(user)
    )


# User settings: {"send_timetable_new_week": false, "send_timetable_updated": false, "send_changes_updated": false}


@router.callback_query(F.data.contains("setting"))
async def settings_handler(call: CallbackQuery):
    setting_name = (
        call.data.replace("_setting", "").replace("disable_", "").replace("enable_", "")
    )
    setting_condition = False if call.data.split("_")[0] == "disable" else True
    user = await get_user_by_id(call.from_user.id)
    user_settings = user.settings
    user_settings_copy = user_settings.copy()
    try:
        user_settings_copy[setting_name] = not setting_condition
    except KeyError:
        print(f"Setting '{setting_name}' not found")
    user = await update_user(call.from_user.id, settings=user_settings_copy)
    updated_kb = await kb.get_settings_keyboard(user)
    await call.message.edit_reply_markup(reply_markup=updated_kb)


@router.callback_query(F.data.contains("_changes"), ShowChanges.changes_data)
async def _(call: CallbackQuery, state: FSMContext):
    condition = call.data.split("_")[0]
    match condition:
        case "show":
            await call.message.delete()
            await call.bot.send_chat_action(call.from_user.id, "upload_photo")
            data = await state.get_data()
            changes_data = data["changes_data"]
            caption = changes_data["caption"]
            media = changes_data["media"]
            if len(media) == 1:
                await call.message.bot.send_photo(
                    call.from_user.id, media[0], caption=caption, parse_mode="html"
                )
            elif len(media) > 1:
                media[0].caption = caption
                media[0].parse_mode = "html"
                await call.message.bot.send_media_group(call.from_user.id, media=media)
        case "dont-show":
            await call.message.delete()
    await state.clear()


@router.callback_query(F.data == "clear-recent-groups")
async def _(call: CallbackQuery):
    user = await get_user_by_id(call.from_user.id)
    user = await update_user(call.from_user.id, recent_groups=None)
    await call.message.edit_reply_markup(
        reply_markup=await kb.get_settings_keyboard(user)
    )
    await call.message.answer(
        "<i>Список последних групп очищен.</i>", parse_mode="html"
    )


@router.callback_query(F.data == "sources")
async def _(call: CallbackQuery):
    await call.message.answer(
        """
Источники:
Расписание - https://time.ulstu.ru/timetable
Список групп - https://time.ulstu.ru/groups
Список преподавателей - https://time.ulstu.ru/teachers
Изменения - https://ulstu.ru/education/spo/kei/student/schedule
"""
    )


@router.message(F.text == "bob6061")
async def _(msg: Message, state: FSMContext):
    if msg.from_user.id == 1522039516:
        await state.set_state(SendToAllAdmin.text)
        await msg.answer(
            "<b>Напишите сообщение которое хотите отправить всем</b>", parse_mode="html"
        )


@router.message(SendToAllAdmin.text)
async def _(msg: Message, state: FSMContext):
    users = await get_users()
    await msg.send_copy(1522039516)
    await asyncio.sleep(15)
    for user in users:
        if user.tg_id != 1579774985:
            try:
                await msg.send_copy(user.tg_id)
                await asyncio.sleep(0.05)
            except Exception as e:
                print(f"Не удалось отправить сообщение пользователю {user.tg_id}: {e}")
    await state.clear()


@router.message()
async def _(msg: Message):
    group_name = msg.text.strip()
    if await get_group_by_name(group_name):
        await fetch_screenshot_path_and_send(group_name, "full", msg)
