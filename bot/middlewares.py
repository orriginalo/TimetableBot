from utils.log import logger
from typing import Any, Dict, Callable, Awaitable
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Filter

from bot.database.queries.user import add_user, get_user_by_id, update_user

from rich import print

from aiogram import Bot


class CheckState(Filter):
    async def __call__(self, message: Message, bot: Bot, state: FSMContext) -> bool:
        user = await get_user_by_id(message.from_user.id)
        if user:
            if (user.group_name is None) and ((await state.get_state()) != 'SetGroup:group_name') and (message.text != '/start'):
                return False
            return True
        return True


class MsgLoggerMiddleware(BaseException):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        user = await get_user_by_id(event.from_user.id)
        if user is None:
            user = await add_user(
                tg_id=event.from_user.id,
                role=1,
                username=event.from_user.username,
                firstname=event.from_user.first_name,
                lastname=event.from_user.last_name,
                group_id=None,
            )
        else:
            if user.role == 0:
                return  # Прерываем выполнение, если роль 0

        # Обновляем данные пользователя в БД
        await update_user(
            event.from_user.id,
            username=event.from_user.username,
            firstname=event.from_user.first_name,
            lastname=event.from_user.last_name,
        )

        # Добавляем пользователя в data
        data['user'] = user
        msg = ''

        # Определяем имя пользователя
        user_name = f'{event.from_user.first_name or ""}{" " + event.from_user.last_name if event.from_user.last_name else ""}'

        try:
            if isinstance(event, Message):
                msg = event.text if event.content_type == 'text' else f'some <{event.content_type}>'
                logger.info(f'Message  - [{user_name}] - "{msg}"')

            elif isinstance(event, CallbackQuery):
                data['callback_data'] = event.data  # Не перезаписываем весь `data`
                msg = ''

                if event.message.reply_markup and event.message.reply_markup.inline_keyboard:
                    for line in event.message.reply_markup.inline_keyboard:
                        for button in line:
                            if button.callback_data == event.data:
                                msg = button.text
                                break

                logger.info(f'Callback - [{user_name}] - "{msg}" : {event.data}')

        except Exception as e:
            print(f'Ошибка в логировании: {e}')

        return await handler(event, data)  # `data` остаётся словарём!
