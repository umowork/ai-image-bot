"""
Balance and payment handlers.
"""
from __future__ import annotations

import logging

from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from config import Config
from models import Database
from services.payment_service import PaymentService

logger = logging.getLogger(__name__)


def register_balance(
    dp: Dispatcher,
    db: Database,
    payment_service: PaymentService,
    config: Config,
) -> None:
    @dp.message(F.text == "💰 Баланс")
    @dp.message(Command("balance"))
    async def btn_balance(message: Message) -> None:
        user = await db.get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name,
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="💳 100₽ (10 кредитов)", callback_data="pay_100"
            )],
            [InlineKeyboardButton(
                text="💳 500₽ (60 кредитов)", callback_data="pay_500"
            )],
        ])
        await message.answer(
            f"💰 Твой баланс: <b>{user.balance:.0f}</b> кредитов\n\n"
            f"1 генерация = 1 кредит\n\n"
            f"Выбери пакет для пополнения:",
            reply_markup=kb,
        )

    @dp.callback_query(F.data.startswith("pay_"))
    async def process_payment(callback: CallbackQuery) -> None:
        amount = int(callback.data.split("_")[1])
        credits = 10 if amount == 100 else 60

        user = await db.get_or_create_user(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
            full_name=callback.from_user.full_name,
        )

        try:
            payment = await payment_service.create_payment(
                amount=float(amount),
                description=f"Пополнение на {amount}₽ ({credits} кредитов)",
                metadata={"user_id": str(user.id), "credits": str(credits)},
            )

            # Save payment record
            await db.create_payment_record(
                user_id=user.id,
                amount=float(amount),
                description=f"Пополнение {amount}₽",
                yookassa_id=payment.get("id"),
            )

            conf_url = payment.get("confirmation", {}).get(
                "confirmation_url",
                payment.get("confirmation_url", ""),
            )

            await callback.message.answer(
                f"💳 <b>Оплата {amount}₽</b>\n\n"
                f"Ты получишь <b>{credits}</b> кредитов.\n\n"
                f"Ссылка для оплаты:\n{conf_url}\n\n"
                f"<i>После оплаты баланс обновится автоматически "
                f"(через webhook).</i>"
            )
        except Exception as e:
            logger.error("payment creation failed: %s", e)
            await callback.message.answer(
                f"❌ Ошибка создания платежа: {e}\n"
                f"Попробуй позже или свяжись с поддержкой."
            )

        await callback.answer()

    @dp.message(F.text == "📜 История")
    @dp.message(Command("history"))
    async def btn_history(message: Message) -> None:
        user = await db.get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name,
        )
        gens = await db.get_user_generations(user.id, limit=10)
        if not gens:
            await message.answer(
                "📭 История пуста. Сгенерируй что-нибудь!"
            )
            return
        lines = []
        for g in gens:
            icon = "🎨" if g.type == "image" else "🎬"
            status = "✅" if g.status == "done" else "⏳"
            lines.append(f"{icon} <code>{g.prompt[:40]}...</code> {status} (-{g.cost:.0f})")
        await message.answer(
            "📜 Последние генерации:\n\n" + "\n".join(lines)
        )
