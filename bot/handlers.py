from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command

import bot.keyboards as kb

router = Router()

@router.message(CommandStart())
async def start_handler(msg: Message):
  await msg.answer("Hi!", reply_markup=kb.main_keyboard)