from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💼 Баланс"), KeyboardButton(text="🛍 Магазин")],
        [KeyboardButton(text="📤 Зняття"), KeyboardButton(text="📜 Історія")],
        [KeyboardButton(text="📘 Покупки"), KeyboardButton(text="🏆 Аукціон")]
    ],
    resize_keyboard=True
)
