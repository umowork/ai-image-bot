"""
Start and help handlers.
"""
from __future__ import annotations

import logging

from aiogram import Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup

from models import Database
from services.referral_service import ReferralService

logger = logging.getLogger(__name__)


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎨 Генерация"), KeyboardButton(text="💰 Баланс")],
            [KeyboardButton(text="📜 История"), KeyboardButton(text="🔗 Рефералка")],
            [KeyboardButton(text="❓ Помощь")],
        ],
        resize_keyboard=True,
    )


def register_start(
    dp: Dispatcher, db: Database, referral_service: ReferralService
) -> None:
    @dp.message(CommandStart())
    async def cmd_start(message: Message, state: FSMContext) -> None:
        await state.clear()

        # Check for referral in deep link
        args = message.text.split()
        referral_code = None
        if len(args) > 1:
            arg = args[1]
            if arg.startswith("ref_"):
                referral_code = arg[4:]

        user = await db.get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name,
            referral_code_from=referral_code,
        )

        text = (
            f"👋 Привет, <b>{user.full_name}</b>!\n\n"
            f"🎨 Я бот для генерации изображений через ИИ.\n"
            f"💰 Баланс: <b>{user.balance:.0f}</b> кредитов\n\n"
            f"Выбери действие в меню."
        )
        await message.answer(text, reply_markup=main_menu())

    @dp.message(F.text == "❓ Помощь")
    @dp.message(Command("help"))
    async def cmd_help(message: Message) -> None:
        await message.answer(
            "🎨 <b>Генерация изображений</b> — 1 кредит\n"
            "💰 <b>Пополнение</b> — через ЮKassa\n"
            "🔗 <b>Рефералка</b> — +5 кредитов за друга\n"
            "📜 <b>История</b> — последние генерации\n\n"
            "По вопросам: @umawork_lab",
            reply_markup=main_menu(),
        )
