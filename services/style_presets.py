"""
Style presets and resolution options for image generation.
Matches competitor features (Click-Click, Bananogen, MagiaPic).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StylePreset:
    id: str
    name: str
    emoji: str
    prompt_prefix: str
    description: str


@dataclass(frozen=True)
class Resolution:
    id: str
    name: str
    size: str  # API-compatible size string
    description: str


# 16 style presets — covers what competitors offer
STYLE_PRESETS: list[StylePreset] = [
    StylePreset(
        "none", "Без стиля", "🎨", "",
        "Чистая генерация без стилевых модификаторов",
    ),
    StylePreset(
        "realistic", "Фотореализм", "📷",
        "photorealistic, ultra-detailed, 8k, DSLR quality,",
        "Реалистичные фото",
    ),
    StylePreset(
        "anime", "Аниме", "🌸",
        "anime style, detailed anime illustration,",
        "Японский аниме-стиль",
    ),
    StylePreset(
        "oil", "Масло", "🖌️",
        "oil painting, classical art style, rich textures,",
        "Классическая живопись маслом",
    ),
    StylePreset(
        "watercolor", "Акварель", "💧",
        "watercolor painting, soft colors, artistic,",
        "Акварельная живопись",
    ),
    StylePreset(
        "pixel", "Пиксель-арт", "👾",
        "pixel art, retro game style, 16-bit,",
        "Ретро пиксельная графика",
    ),
    StylePreset(
        "cyberpunk", "Киберпанк", "🌆",
        "cyberpunk style, neon lights, futuristic city,",
        "Неоновое будущее",
    ),
    StylePreset(
        "fantasy", "Фэнтези", "🐉",
        "fantasy art, magical, epic, detailed illustration,",
        "Магический фэнтези-мир",
    ),
    StylePreset(
        "minimal", "Минимализм", "◻️",
        "minimalist design, clean lines, simple,",
        "Чистый минимализм",
    ),
    StylePreset(
        "3d", "3D-рендер", "🧊",
        "3D render, cinema 4D style, octane render,",
        "Трёхмерная графика",
    ),
    StylePreset(
        "comic", "Комикс", "💥",
        "comic book art style, bold lines, vibrant,",
        "Комиксный стиль",
    ),
    StylePreset(
        "sketch", "Скетч", "✏️",
        "pencil sketch, hand-drawn, detailed linework,",
        "Рисунок карандашом",
    ),
    StylePreset(
        "popart", "Поп-арт", "🎭",
        "pop art style, Andy Warhol inspired, bold colors,",
        "Яркий поп-арт",
    ),
    StylePreset(
        "dark", "Тёмный", "🌑",
        "dark moody atmosphere, dramatic lighting, noir,",
        "Мрачная атмосфера",
    ),
    StylePreset(
        "neon", "Неон", "💡",
        "neon glow, vibrant neon colors, glowing effects,",
        "Неоновое свечение",
    ),
    StylePreset(
        "origami", "Оригами", "🦢",
        "origami style, paper craft, folded paper art,",
        "Бумажное оригами",
    ),
]

# 3 resolutions — DALL-E 3 supported sizes
RESOLUTIONS: list[Resolution] = [
    Resolution(
        "square", "Квадрат 1024×1024", "1024x1024",
        "Стандартный квадрат",
    ),
    Resolution(
        "portrait", "Портрет 1024×1792", "1024x1792",
        "Вертикальный формат",
    ),
    Resolution(
        "landscape", "Альбом 1792×1024", "1792x1024",
        "Горизонтальный формат",
    ),
]


def get_style_by_id(style_id: str) -> StylePreset | None:
    for s in STYLE_PRESETS:
        if s.id == style_id:
            return s
    return None


def get_resolution_by_id(res_id: str) -> Resolution | None:
    for r in RESOLUTIONS:
        if r.id == res_id:
            return r
    return None
