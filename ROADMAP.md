# ROADMAP — 02 ai-image-video-bot

## Шаг 1 — Скелет + image generation

- [ ] aiogram 3 структура (handlers/keyboards/states/services)
- [ ] SQLite: User, Generation, Payment модели
- [ ] Handler `/start` с реферальным кодом
- [ ] DALL-E 3 интеграция
- [ ] Free-trial лимит 3 image/день

## Шаг 2 — Multi-provider image

- [ ] Flux Schnell через Replicate
- [ ] Stable Diffusion XL fallback
- [ ] 5 стилей-пресетов (system prompt + примеры)
- [ ] Inline-keyboard для выбора разрешения

## Шаг 3 — Video generation

- [ ] Kling / Seedance API (через российских реселлеров если нужно)
- [ ] Text-to-video и image-to-video режимы
- [ ] Лимит длины (3-10с)
- [ ] Отдельный лимит free-trial для video

## Шаг 4 — ЮKassa оплата

- [ ] ЮKassa sandbox setup
- [ ] 4 пакета: image+video комбо
- [ ] Webhook endpoint через aiohttp
- [ ] Начисление кредитов после оплаты
- [ ] История платежей: `/history`

## Шаг 5 — Реферальная программа + админ

- [ ] При /start с реф-кодом → +10 кредитов обоим
- [ ] Top рефереров: `/top_refs`
- [ ] Админ-команды: `/stats`, `/broadcast`, `/give_credits`
- [ ] Whitelisted user_id для админки

## Шаг 6 — Polish + деплой

- [ ] Docker compose
- [ ] Deploy на Fly.io
- [ ] Тестовый бот публично доступен
- [ ] README с реальными метриками (cost, latency, конверсия)
- [ ] Loom-демка
- [ ] Tag `v1.0.0`
