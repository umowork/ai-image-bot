"""
Generate image handler — full-featured version with:
- Style presets (16 styles)
- Resolution picker (3 sizes)
- NSFW content filter
- Background queue (non-blocking)
- Daily free-trial limit (3/day)
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime

from aiogram import Dispatcher, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from models import Database
from services.content_filter import ContentFilter
from services.generation_queue import GenerationJob, GenerationQueue
from services.image_service import IMAGE_COST
from services.style_presets import RESOLUTIONS, STYLE_PRESETS, get_resolution_by_id, get_style_by_id

logger = logging.getLogger(__name__)

DAILY_FREE_LIMIT = 3


class ImageGen(StatesGroup):
    choosing_style = State()
    choosing_resolution = State()
    entering_prompt = State()


def _style_keyboard() -> InlineKeyboardMarkup:
    """Build inline keyboard with style presets (2 per row)."""
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for style in STYLE_PRESETS:
        row.append(
            InlineKeyboardButton(
                text=f"{style.emoji} {style.name}",
                callback_data=f"style_{style.id}",
            )
        )
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _resolution_keyboard() -> InlineKeyboardMarkup:
    """Build inline keyboard with resolution options."""
    rows = [
        [InlineKeyboardButton(
            text=f"📐 {res.name}",
            callback_data=f"res_{res.id}",
        )]
        for res in RESOLUTIONS
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def _get_today_free_count(db: Database, user_id: int) -> int:
    """Count how many free generations user used today."""
    from sqlalchemy import func, select

    from models import Generation

    async with db.session_factory() as session:
        today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        result = await session.execute(
            select(func.count(Generation.id)).where(
                Generation.user_id == user_id,
                Generation.created_at >= today_start,
                Generation.cost == 0.0,
            )
        )
        return result.scalar() or 0


def register_generate(
    dp: Dispatcher, db: Database, image_service_or_queue,
) -> None:
    """Register generation handlers. Accepts either ImageService or GenerationQueue."""

    # Support both old (ImageService) and new (GenerationQueue) interfaces
    queue: GenerationQueue | None = None
    if isinstance(image_service_or_queue, GenerationQueue):
        queue = image_service_or_queue

    @dp.message(F.text == "🎨 Генерация")
    async def btn_generate(message: Message, state: FSMContext) -> None:
        user = await db.get_or_create_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.full_name,
        )

        # Check daily free limit
        today_free = await _get_today_free_count(db, user.id)
        has_free = today_free < DAILY_FREE_LIMIT

        # Check if user has credits or free attempts
        if user.balance < IMAGE_COST and not has_free:
            await message.answer(
                f"❌ Недостаточно кредитов ({user.balance:.0f}) и "
                f"бесплатные генерации исчерпаны "
                f"({DAILY_FREE_LIMIT}/{DAILY_FREE_LIMIT}).\n\n"
                f"💰 Пополни через раздел 'Баланс' или подожди."
            )
            return

        cost_info = ""
        if has_free:
            remaining = DAILY_FREE_LIMIT - today_free
            cost_info = f"🎁 Бесплатных сегодня: {remaining}/{DAILY_FREE_LIMIT}\n"
        else:
            cost_info = f"💳 Стоимость: {IMAGE_COST} кредит\n"

        await state.set_state(ImageGen.choosing_style)
        await message.answer(
            f"🎨 <b>Генерация изображения</b>\n\n"
            f"{cost_info}\n"
            f"Шаг 1/3: Выбери стиль:",
            reply_markup=_style_keyboard(),
        )

    @dp.callback_query(F.data.startswith("style_"))
    async def choose_style(callback: CallbackQuery, state: FSMContext) -> None:
        style_id = callback.data.replace("style_", "")
        style = get_style_by_id(style_id)
        if not style:
            await callback.answer("Неизвестный стиль")
            return

        await state.update_data(style_id=style_id)
        await state.set_state(ImageGen.choosing_resolution)

        await callback.message.edit_text(
            f"🎨 Стиль: {style.emoji} {style.name}\n\n"
            f"Шаг 2/3: Выбери разрешение:",
            reply_markup=_resolution_keyboard(),
        )
        await callback.answer()

    @dp.callback_query(F.data.startswith("res_"))
    async def choose_resolution(callback: CallbackQuery, state: FSMContext) -> None:
        res_id = callback.data.replace("res_", "")
        resolution = get_resolution_by_id(res_id)
        if not resolution:
            await callback.answer("Неизвестное разрешение")
            return

        await state.update_data(resolution_id=res_id)
        await state.set_state(ImageGen.entering_prompt)

        data = await state.get_data()
        style = get_style_by_id(data["style_id"])

        await callback.message.edit_text(
            f"🎨 Стиль: {style.emoji} {style.name}\n"
            f"📐 Разрешение: {resolution.name}\n\n"
            f"Шаг 3/3: Опиши, что нарисовать:\n\n"
            f"<i>Например: кот в космосе, неоновый стиль, 4K</i>\n\n"
            f"Для отмены: /cancel"
        )
        await callback.answer()

    @dp.message(ImageGen.entering_prompt)
    async def process_prompt(message: Message, state: FSMContext) -> None:
        if message.text == "/cancel":
            await state.clear()
            await message.answer("❌ Генерация отменена.", reply_markup=None)
            return

        data = await state.get_data()
        await state.clear()

        style_id = data.get("style_id", "none")
        resolution_id = data.get("resolution_id", "square")
        style = get_style_by_id(style_id)
        resolution = get_resolution_by_id(resolution_id)

        # NSFW filter
        is_safe, reason = ContentFilter.is_safe(message.text)
        if not is_safe:
            await message.answer(f"🚫 {reason}. Попробуй другой промпт.")
            return

        user = await db.get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name,
        )

        # Determine cost: free or paid
        today_free = await _get_today_free_count(db, user.id)
        is_free = today_free < DAILY_FREE_LIMIT
        cost = 0.0 if is_free else IMAGE_COST

        if cost > 0 and user.balance < cost:
            await message.answer(
                f"❌ Недостаточно кредитов. Нужно: {cost}, у тебя: {user.balance:.0f}\n"
                f"Пополни через раздел 'Баланс'."
            )
            return

        # Deduct balance (skip if free)
        if cost > 0:
            success = await db.deduct_balance(user.id, cost)
            if not success:
                await message.answer("❌ Ошибка списания кредитов")
                return

        # Create generation record
        gen = await db.add_generation(
            user.id, "image", message.text, cost
        )

        style_prefix = style.prompt_prefix if style else ""
        size = resolution.size if resolution else "1024x1024"

        # Enqueue to background queue or process inline
        if queue:
            job = GenerationJob(
                user_id=user.id,
                telegram_id=message.from_user.id,
                gen_id=gen.id,
                prompt=message.text,
                style_prefix=style_prefix,
                size=size,
            )
            await queue.enqueue(job)

            free_tag = "🎁 Бесплатно" if is_free else f"💳 {cost:.0f} кредитов"
            await message.answer(
                f"⏳ Генерация в очереди...\n"
                f"🎨 Стиль: "
                f"{style.emoji if style else '🎨'} "
                f"{style.name if style else 'Без стиля'}\n"
                f"📐 {resolution.name if resolution else '1024×1024'}\n"
                f"{free_tag}\n\n"
                f"Результат придёт автоматически."
            )
        else:
            # Fallback: inline generation (blocks bot)
            progress = await message.answer("🎨 Генерирую изображение...")
            try:
                full_prompt = (
                    f"{style_prefix} {message.text}".strip()
                    if style_prefix else message.text
                )
                result = await image_service_or_queue.generate(full_prompt, size=size)
                await db.update_generation(gen.id, result["url"], "done")
                await progress.delete()

                free_tag = "🎁 Бесплатно" if is_free else f"💳 {cost:.0f}"
                await message.answer_photo(
                    photo=result["url"],
                    caption=(
                        f"✅ Готово!\n"
                        f"🎨 {style.emoji if style else ''} {style.name if style else ''}\n"
                        f"📐 {resolution.name if resolution else ''}\n"
                        f"{free_tag}"
                    ),
                )
            except Exception as e:
                if cost > 0:
                    await db.add_balance(user.id, cost)  # refund
                await progress.edit_text(f"❌ Ошибка генерации: {e}")
                logger.error("image generation failed: %s", e)
