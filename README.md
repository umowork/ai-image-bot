# AI Image Bot

> 🎨 Telegram-бот для генерации **картинок** с ЮKassa-оплатой, реферальной программой и 16 стилями.

## Для бизнеса

**Что это:** Готовый Telegram-бот, который генерирует изображения по запросу через ИИ. Пользователи платят за пакеты, владелец получает доход на автопилоте.

**Категория спроса:** массовый TG-сегмент — Click-Click, Bananogen, MagiaPic, TrendAI, FOX AI стабильно держатся в ТОП-10 ботов с рефералкой 2026 (источник: dtf.ru).

**Кому пригодится:**
- 💼 Предпринимателям — запустить как side-business
- 🎨 SMM-агентствам — внутренний инструмент
- 📱 Контент-мейкерам — быстрые материалы

**Что получают:**
- ✅ Готовый бот с их брендингом
- ✅ Image generation (DALL-E 3 / Flux Schnell) с fallback
- ✅ 16 стилей-пресетов (реализм, аниме, масло, киберпанк, пиксель-арт и др.)
- ✅ 3 разрешения (квадрат, портрет, альбом)
- ✅ ЮKassa тарифы (100₽/500₽)
- ✅ Реферальная программа из коробки
- ✅ Бесплатный лимит: 3 генерации/день
- ✅ NSFW-фильтр на промптах
- ✅ Rate limiting (антифлуд)
- ✅ Background queue (3 параллельных воркера)
- ✅ Аналитика заказов

**Цена внедрения:** 2 000 — 15 000 ₽ + LTV от подписок

---

## Для разработчика

**Стек:**
- Python 3.12 + **aiogram 3.13**
- SQLite (для простоты) или PostgreSQL (при масштабировании)
- MemoryStorage для FSM (in-memory, production: Redis)
- **OpenAI DALL-E 3** + **Flux Schnell** (Replicate) — image generation
- **ЮKassa Python SDK** — оплата
- Pillow — постобработка

**Архитектура:**
```
[Telegram User] → [Rate Limit Middleware] → [aiogram handlers]
                         ↓
                    [NSFW Content Filter]
                         ↓
                    [Style + Resolution Picker]
                         ↓
                 [Generation Queue (asyncio, 3 workers)]
                         ↓
                 [DALL-E / Flux API]
                         ↓
              [SQLite: users, payments, history]
                         ↓
              [ЮKassa webhook handler]
                         ↓
              [Referral logic +5 за приглашённого]
```

**Фичи (реализовано):**
- Image: prompt-based generation, 3 разрешения, провайдеры DALL-E 3 + Flux Schnell с fallback
- 16 стилей-пресетов с inline-кнопками
- ЮKassa тарифы и реферальная программа (`+5` рефереру, `+10` бонус новому юзеру)
- Бесплатный лимит: 3 генерации/день (сбрасывается ежедневно)
- NSFW-фильтр на промптах (блокирует запрещённый контент)
- Rate limiting middleware (5 сообщений / 10 секунд)
- Background queue (asyncio.Queue, 3 параллельных воркера)
- Admin-команды: `/stats`, `/broadcast`, `/give_credits`
- История генераций в SQLite

## Быстрый старт

```bash
cp .env.example .env
# Заполнить: BOT_TOKEN, OPENAI_API_KEY (или REPLICATE_API_TOKEN)
pip install -r requirements.txt
python -m bot.bot
```

## Тесты

```bash
pip install -r requirements-test.txt
python3 -m pytest tests/ -v
```

## Деплой

- **Docker Compose** — `docker compose up`
- **Fly.io** — с persistent volume для Telethon-сессий

---

## Стили-пресеты

| Стиль | Описание |
|-------|----------|
| 🎨 Без стиля | Чистая генерация |
| 📷 Фотореализм | Реалистичные фото, 8K |
| 🌸 Аниме | Японский аниме-стиль |
| 🖌️ Масло | Классическая живопись |
| 💧 Акварель | Акварельная живопись |
| 👾 Пиксель-арт | Ретро 16-бит |
| 🌆 Киберпанк | Неоновое будущее |
| 🐉 Фэнтези | Магический мир |
| ◻️ Минимализм | Чистые линии |
| 🧊 3D-рендер | Cinema 4D, Octane |
| 💥 Комикс | Комиксный стиль |
| ✏️ Скетч | Карандашный рисунок |
| 🎭 Поп-арт | Энди Уорхол |
| 🌑 Тёмный | Мрачная атмосфера |
| 💡 Неон | Неоновое свечение |
| 🦢 Оригами | Бумажное искусство |

## Roadmap

### Шаг 1 — MVP ✅ DONE
- [x] FastAPI backend с REST API
- [x] Image generation: DALL-E 3 + Flux Schnell с fallback
- [x] ЮKassa webhook + inline-оплата
- [x] Реферальная программа
- [x] 16 стилей-пресетов
- [x] 3 разрешения
- [x] NSFW-фильтр
- [x] Rate limiting
- [x] Background queue (3 workers)
- [x] Бесплатный лимит (3/день)
- [x] Тесты (30 тестов)
- [x] Docker Compose

### Шаг 2 — Продакшн
- [ ] Telegram Stars (альтернатива ЮKassa)
- [ ] Мультиязычность (EN, ES, DE)
- [ ] Inline-режим (@bot prompt)
- [ ] Статистика для админа (dashboard)

### Шаг 3 — Расширения
- [ ] LoRA-кастомизация на фото пользователя
- [ ] Inpainting (редактирование части картинки)
- [ ] A/B тесты стилей
- [ ] Webhook-интеграция в чужой сервис

## Правовые дисклеймеры

- DALL-E / Flux ToS: коммерческое использование с ограничениями — изучить
- Лица реальных людей без согласия — запрещено
- NSFW: фильтрация на уровне приложения + провайдера
- При перепродаже бота — лицензионное соглашение с заказчиком

---

*Built with AI assistance.*
