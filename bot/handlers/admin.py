"""
Admin commands: /stats, /broadcast, /give_credits.
"""
from __future__ import annotations

import logging

from aiogram import Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

from models import Database

logger = logging.getLogger(__name__)


def is_admin(admin_ids: list[int]):
    """Return a filter that checks if message.from_user.id is in admin_ids."""
    async def _check(message: Message) -> bool:
        return message.from_user.id in admin_ids
    return _check


def register_admin(
    dp: Dispatcher,
    db: Database,
    admin_ids: list[int],
) -> None:
    """Register admin-only command handlers."""

    admin_filter = is_admin(admin_ids)

    @dp.message(Command("stats"), admin_filter)
    async def cmd_stats(message: Message) -> None:
        """Show bot statistics: user count, total generations, revenue."""
        stats = await db.get_stats()
        text = (
            "📊 <b>Статистика бота</b>\n\n"
            f"👥 Пользователей: <b>{stats['users']}</b>\n"
            f"🖼 Генераций: <b>{stats['generations']}</b>\n"
            f"💰 Выручка: <b>{stats['revenue']:.2f}</b> ₽\n"
        )
        await message.answer(text)

    @dp.message(Command("broadcast"), admin_filter)
    async def cmd_broadcast(message: Message) -> None:
        """Broadcast a message to all users.
        Usage: /broadcast <text>
        """
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            await message.answer(
                "❌ Использование: /broadcast <текст сообщения>"
            )
            return

        broadcast_text = parts[1]
        users = await db.get_all_users()
        sent = 0
        failed = 0
        for user in users:
            try:
                await message.bot.send_message(
                    chat_id=user.telegram_id,
                    text=f"📢 <b>Объявление</b>\n\n{broadcast_text}",
                )
                sent += 1
            except Exception:
                failed += 1

        await message.answer(
            f"✅ Рассылка завершена.\n"
            f"Отправлено: {sent}, ошибок: {failed}"
        )

    @dp.message(Command("give_credits"), admin_filter)
    async def cmd_give_credits(message: Message) -> None:
        """Add credits to a user.
        Usage: /give_credits <telegram_id> <amount>
        """
        parts = message.text.split()
        if len(parts) != 3:
            await message.answer(
                "❌ Использование: /give_credits <telegram_id> <количество>"
            )
            return

        try:
            target_telegram_id = int(parts[1])
            amount = float(parts[2])
        except ValueError:
            await message.answer("❌ Неверный формат. Используйте числа.")
            return

        if amount <= 0:
            await message.answer("❌ Количество должно быть положительным.")
            return

        user = await db.get_user_by_telegram_id(target_telegram_id)
        if not user:
            await message.answer(
                f"❌ Пользователь с ID {target_telegram_id} не найден."
            )
            return

        updated = await db.add_balance(user.id, amount)
        await message.answer(
            f"✅ Начислено <b>{amount:.0f}</b> кредитов "
            f"пользователю <b>{updated.full_name}</b> "
            f"(ID: {target_telegram_id}).\n"
            f"Новый баланс: <b>{updated.balance:.0f}</b>"
        )
