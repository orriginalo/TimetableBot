from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.database.schemas import UserSchema

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="⏭️ След. неделя"),
            KeyboardButton(text="Текущая неделя ⬅️"),
        ],
        [KeyboardButton(text="⏭️ Завтра"), KeyboardButton(text="Сегодня ⬅️")],
        [KeyboardButton(text="📋 Изменения"), KeyboardButton(text="Настройки 🔧")],
        [KeyboardButton(text="❔Расписание другой группы❔")],
    ],
    resize_keyboard=True,
    input_field_placeholder="Что ты хочешь узнать?",
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
        [
            InlineKeyboardButton(
                text="⏭️ Следующая", callback_data="next-week_other_group"
            ),
            InlineKeyboardButton(
                text="Текущая ⬅️", callback_data="current-week_other_group"
            ),
        ],
    ]
)

empty_inline = InlineKeyboardMarkup(inline_keyboard=[])


async def get_recent_groups_keyboard(user: UserSchema):
    groups = user.recent_groups
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="« Назад", callback_data="back"))
    if groups and len(groups) > 0:
        for group in groups:
            kb.add(
                InlineKeyboardButton(
                    text=group.capitalize(), callback_data=f"see-other-group_{group}"
                )
            )
    return kb.adjust(3).as_markup()


async def get_settings_keyboard(user: UserSchema):
    def get_emoji_by_bool(var: bool):
        return "✅" if var else "❌"

    def get_callback_by_bool(var: bool):
        return "enable_" if var else "disable_"

    settings_postfix = "_setting"

    timetable_settings = [
        {"key": "send_timetable_new_week", "label": "Расписание с новой недели 🗓"},
    ]
    changes_settings = [
        {"key": "send_changes_updated", "label": "Новые изменения 📋"},
        {
            "key": "send_changes_when_isnt_group",
            "label": "Присылать изменения когда группы нет",
        },
        {
            "key": "only_page_with_group_in_changes",
            "label": "Только страница с группой в изменениях",
        },
    ]

    kb = InlineKeyboardBuilder()

    kb.add(InlineKeyboardButton(text="🔄️ Сменить группу", callback_data="change-group"))
    if user.recent_groups:
        kb.add(
            InlineKeyboardButton(
                text="🔄 Сбросить последние группы", callback_data="clear-recent-groups"
            )
        )

    for setting in timetable_settings:
        key = setting["key"]
        label = setting["label"]
        value = user.settings.get(key, False)  # По умолчанию False, если нет ключа
        kb.add(
            InlineKeyboardButton(
                text=f"{get_emoji_by_bool(value)} {label}",
                callback_data=f"{get_callback_by_bool(value)}{key}{settings_postfix}",
            )
        )

    for setting in changes_settings:
        key = setting["key"]
        label = setting["label"]
        value = user.settings.get(key, False)  # По умолчанию False, если нет ключа
        kb.add(
            InlineKeyboardButton(
                text=f"{get_emoji_by_bool(value)} {label}",
                callback_data=f"{get_callback_by_bool(value)}{key}{settings_postfix}",
            )
        )
    # feat: обновлены настройки для отправки изменений и добавлены новые параметры
    # Кнопка назад
    kb.add(InlineKeyboardButton(text="Источники", callback_data="sources"))
    kb.add(InlineKeyboardButton(text="« Назад", callback_data="back-settings"))

    return kb.adjust(1).as_markup()
