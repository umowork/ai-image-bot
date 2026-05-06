"""
Referral handler.
"""
from __future__ import annotations

import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

from models import Database

logger = logging.getLogger(__name__)


def register_referral(dp: Dispatcher, db: Database, bot: Bot) -> None:
    @dp.message(F.text == "🔗 Рефералка")
    @dp.message(Command("refer"))
    async def btn_referral(message: Message) -> None:
        user = await db.get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name,
        )
        bot_info = await bot.get_me()
        link = f"https://t.me/{bot_info.username}?start=ref_{user.referral_code}"
        await message.answer(
            f"🔗 <b>Твоя реферальная ссылка:</b>\n"
            f"<code>{link}</code>\n\n"
            f"Приглашай друзей — получай <b>+5 кредитов</b> за каждого!\n"
            f"Новый пользователь получает <b>+10 кредитов</b> "
            f"при регистрации по ссылке.\n\n"
            f"<i>Ссылку можно отправлять друзьям, "
            f"публиковать в соцсетях и каналах.</i>"
        )
