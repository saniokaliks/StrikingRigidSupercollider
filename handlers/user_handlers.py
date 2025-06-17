from states import Register
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from data.auction_data import auction, save_auction
from aiogram.filters import Command

from config import ADMINS
from keyboards import main_menu
from database import load_users, save_users
from datetime import datetime, timedelta

router = Router()
from handlers.data.utils.storage import users


    # Стани FSM
class WithdrawState(StatesGroup):
        waiting_for_amount = State()


@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)

    if user_id in users:
        await message.answer("✅ Ви вже зареєстровані!", reply_markup=main_menu)
        return

    # Спочатку вітальне повідомлення
    await message.answer("👋 Ласкаво просимо до RePhrase TEAM! Тут ти можеш стежити за своїм балансом, бонусами та користуватися іншими функціями.")

    # Потім прохання ввести позивний
    await message.answer("👋 Введіть свій позивний:")
    await state.set_state(Register.nickname)

# ❗️ ВИНЕСЕНО З-ПІД start()
@router.message(Register.nickname)
async def register_nickname(msg: Message, state: FSMContext):
        nickname = msg.text.strip()

        if not (2 <= len(nickname) <= 20):
            await msg.answer("❗ Ваш позивний невірний. Введіть від 2 до 20 символів.")
            return

        uid = str(msg.from_user.id)

        if uid in users:
            await msg.answer("✅ Ви вже зареєстровані.")
            await state.clear()
            return

        # Реєстрація нового користувача
        users[uid] = {
            "nickname": nickname,
            "bonus": 500,
            "normal": 0,
            "history": [],
            "last_withdrawal": None,
            "banned": False,
            "frozen": {}
        }
        save_users(users)

        total_users = len(users)

        for admin_id in ADMINS:
            await msg.bot.send_message(
                admin_id,
                f"🆕 Новий користувач\n"
                f"Позивний: {nickname}\n"
                f"ID: {uid}\n"
                f"Загалом користувачів: {total_users}\n"
                f"🎁 Бонус видано: 500 монет"
            )

        await msg.answer("✅ Позивний встановлено! Ви отримали 500 бонусних монет.", reply_markup=main_menu)
        await state.clear()



# Перевірка бану
@router.message(F.text.in_(["💼 Баланс", "📤 Зняття"]))
async def handle_main_options(message: Message, state: FSMContext, bot: Bot):
    user_id = str(message.from_user.id)
    user = users.get(user_id)

    if not user:
        await message.answer("Будь ласка, натисніть /start для реєстрації.")
        return

    if user.get("banned"):
        await message.answer("🚫 Ви заблоковані і не можете користуватись ботом.")
        return

    if message.text == "💼 Баланс":
        await message.answer(
            f"💼 Баланс:\n"
            f"Позивний: {user['nickname']}\n"
            f"ID: {user_id}\n"
            f"🎁 Бонусні монети: {user['bonus']}\n"
            f"💰 Звичайні монети: {user['normal']}"
        )

    elif message.text == "📤 Зняття":
        pending = user.get("pending_withdrawal")
        if pending:
            last_time = datetime.fromisoformat(pending["requested_at"])
            if datetime.now() - last_time < timedelta(days=1):
                await message.answer("❗ Ви вже зробили запит на зняття сьогодні. Очікуйте підтвердження.")
                return
        else:
            last_time_str = user.get("last_withdrawal_time")
            if last_time_str:
                last_time = datetime.fromisoformat(last_time_str)
                if datetime.now() - last_time < timedelta(days=1):
                    await message.answer("❗ Ви вже робили зняття сьогодні. Спробуйте завтра.")
                    return

        await message.answer("✏️ Введіть суму для зняття (від 3000 до 15000):")
        await state.set_state(WithdrawState.waiting_for_amount)


# Обробка введеної суми на зняття
@router.message(WithdrawState.waiting_for_amount, F.text)
async def process_withdraw_amount(message: Message, state: FSMContext, bot: Bot):
    user_id = str(message.from_user.id)
    user = users.get(user_id)

    text = message.text.strip()

    if not text.isdigit():
        await message.answer("❗ Введіть коректне число (від 3000 до 15000).")
        await state.clear()
        return

    amount = int(text)

    if amount < 3000 or amount > 15000:
        await message.answer("❗ Сума повинна бути в межах від 3000 до 15000.")
        await state.clear()
        return

    if user["normal"] < amount:
        await message.answer("❌ Недостатньо звичайних монет для зняття.")
        await state.clear()
        return

    # 💰 ВІДНІМАЄМО МОНЕТИ ЗІ ЗВИЧАЙНОГО БАЛАНСУ
    # Зберігаємо запит на зняття, але не знімаємо монети
    user["pending_withdrawal"] = {
        "amount": amount,
        "requested_at": datetime.now().isoformat()
    }
    save_users(users)


    uah = amount / 3
    await message.answer(
        f"✅ Ваш запит на виведення коштів успішно надіслано модератору. Зазвичай обробка займає до 24 годин.Дякуємо за терпіння!.\n"
        f"💸 Приблизна сума: {uah:.2f} грн."
    )
    await state.clear()

    for admin_id in ADMINS:
        await bot.send_message(
            admin_id,
            f"📤 Запит на зняття:\n"
            f"Позивний: {user['nickname']}\n"
            f"ID: {user_id}\n"
            f"Сума: {amount} монет ≈ {uah:.2f} грн.\n"
            f"✅ Прийняти / ❌ Відхилити",
            reply_markup=build_admin_withdraw_buttons(user_id, amount)
        )



# Кнопки для адміна (підтвердження/відхилення)
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def build_admin_withdraw_buttons(user_id: str, amount: int):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Прийняти", callback_data=f"accept:{user_id}:{amount}"),
            InlineKeyboardButton(text="❌ Відхилити", callback_data=f"decline:{user_id}:{amount}")
        ]
    ])
    return markup
@router.message(F.text == "📜 Історія")
async def show_history(message: Message):
    user_id = str(message.from_user.id)
    user = users.get(user_id)

    if not user:
        await message.answer("Користувач не знайдений.")
        return

    if user.get("banned"):
        await message.answer("🚫 Ви заблоковані.")
        return

    history = user.get("history", [])
    if not history:
        await message.answer("📜 У вас поки немає історії виведення.")
    else:
        await message.answer("📜 Історія виводів:\n" + "\n".join(history))
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup

class ShopState(StatesGroup):
    choosing_service = State()
    choosing_wallet = State()
    entering_book_title = State()
SERVICES = {
    1: ("В рекомендації [3 години]", 55),
    2: ("В рекомендації [12 годин]", 200),
    3: ("В рекомендації [24 години]", 350),
    4: ("На головній [3 години]", 250),
    5: ("На головній [12 годин]", 1000),
    6: ("На головній [24 години]", 2000),
    7: ("В каталозі [24 години]", 350),
    8: ("За жанрами [24 години]", 150),
    9: ("За тегами [24 години]", 100),
    10: ("За фeндомами [24 години]", 150),
    11: ("Вся реклама на [24 години]", 2800),
    12: ("В соцмережах [24 години]", 2000),
    13: ("Озвучка книги [1 розділ]", 300),
    14: ("Генерація заставки [1 фото]", 300),
    15: ("Редагування [1 розділ]", 200),
    16: ("Випуск [1 розділ]", 300),
    17: ("Випуск [5 розділ]", 1000),
}
@router.message(F.text == "🛍 Магазин")
async def open_shop(message: Message, state: FSMContext):
    if users.get(str(message.from_user.id), {}).get("banned"):
        await message.answer("🚫 Ви заблоковані та не можете користуватись магазином.")
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{key}: {name} - {price} монет", callback_data=f"shop:{key}")]
        
        for key, (name, price) in SERVICES.items()
    ])
    await message.answer("🛍 Оберіть послугу:", reply_markup=kb)
    await state.set_state(ShopState.choosing_service)
@router.callback_query(ShopState.choosing_service, F.data.startswith("shop:"))
async def select_service(callback: CallbackQuery, state: FSMContext):
    service_id = int(callback.data.split(":")[1])
    service_name, price = SERVICES[service_id]

    await state.update_data(service_id=service_id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎁 Бонусний баланс", callback_data="wallet:bonus"),
            InlineKeyboardButton(text="💰 Звичайний баланс", callback_data="wallet:normal")
        ]
    ])
    await callback.message.edit_text(f"🔄 Ви обрали: {service_name}.\n💳 З якого балансу сплатити?", reply_markup=kb)
    await state.set_state(ShopState.choosing_wallet)
@router.callback_query(ShopState.choosing_wallet, F.data.startswith("wallet:"))
async def choose_wallet(callback: CallbackQuery, state: FSMContext):
    wallet_type = callback.data.split(":")[1]
    await state.update_data(wallet=wallet_type)
    await callback.message.edit_text("📘 Введіть назву книги:")
    await state.set_state(ShopState.entering_book_title)
@router.message(ShopState.entering_book_title)
async def enter_book_title(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    service_id = data["service_id"]
    wallet_type = data["wallet"]
    book_title = message.text.strip()

    service_name, price = SERVICES[service_id]
    user_id = str(message.from_user.id)
    user = users[user_id]

    balance = user[wallet_type]
    if balance < price:
        await message.answer("❗ Недостатньо монет на балансі.")
        await state.clear()
        return

    user[wallet_type] -= price
    user.setdefault("purchases", []).append({
        "service": service_name,
        "book": book_title,
        "wallet": "🎁 Бонусний" if wallet_type == "bonus" else "💰 Звичайний",
        "price": price
    })
    save_users(users)

    await message.answer(f"✅ Замовлення оформлено. Послуга: {service_name}\n📘 Книга: {book_title}")
    await state.clear()

    for admin_id in ADMINS:
        await bot.send_message(
            admin_id,
            f"📥 Нова покупка послуги:\n"
            f"ID: {user_id}\n"
            f"Позивний: {user['nickname']}\n"
            f"Послуга: {service_name}\n"
            f"Баланс: {wallet_type.upper()}\n"
            f"Назва книги: {book_title}\n"
            f"Списано: {price} монет"
        )
@router.message(F.text == "📘 Покупки")
async def show_purchases(message: Message):
    user_id = str(message.from_user.id)
    user = users.get(user_id)
    if users.get(str(message.from_user.id), {}).get("banned"):
        await message.answer("🚫 Ви заблоковані та не можете користуватись цими функціями.")
        return


    if not user:
        await message.answer("Користувача не знайдено.")
        return

    purchases = user.get("purchases", [])
    if not purchases:
        await message.answer("📘 У вас поки немає покупок.")
        return

    history_text = "\n\n".join([f"📦 {p['service']}\n📘 {p['book']}\n💳 {p['wallet']} - {p['price']} монет" for p in purchases])
    await message.answer(f"📘 Ваші покупки:\n\n{history_text}")

@router.message(F.text == "🏆 Аукціон")
async def open_auction(message: Message):
    if users.get(str(message.from_user.id), {}).get("banned"):
        await message.answer("🚫 Ви заблоковані та не можете користуватись цими функціями.")
        return

    if not auction:
        await message.answer("📚 Зараз немає активних аукціонів.")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{book_id}", callback_data=f"auction:{book_id}")]
        for book_id in auction
    ])
    await message.answer("📘 Оберіть книгу для перегляду аукціону:", reply_markup=kb)

from datetime import datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@router.callback_query(F.data.startswith("auction:"))
async def view_auction(callback: CallbackQuery):
    book_id = callback.data.split(":")[1]
    data = auction[book_id]
    desc = data['description']
    bid = data['highest_bid']
    user = data['highest_user']

    # ⏳ Обрахунок часу
    remaining = "—"
    end_time_str = data.get("end_time")
    if end_time_str:
        end_time = datetime.fromisoformat(end_time_str)
        delta = end_time - datetime.now()

        if delta.total_seconds() > 0:
            minutes = delta.seconds // 60
            seconds = delta.seconds % 60
            remaining = f"{minutes} хв {seconds} сек"
        else:
            remaining = "Завершено"

    text = (
        f"📖 Книга: {book_id}\n"
        f"📄 Опис: {desc}\n"
        f"💰 Найвища ставка: {bid if bid > 0 else '—'}\n"
        f"🔻 Мінімальна ставка: {data['min_bid']}\n"
        f"⏳ Час до завершення: {remaining}"
    )

    btn = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💸 Зробити ставку", callback_data=f"bid:{book_id}")]
    ])

    await callback.message.edit_text(text, reply_markup=btn)

class BidState(StatesGroup):
    choosing_balance = State()
    entering_amount = State()

@router.callback_query(F.data.startswith("bid:"))
async def start_bid(callback: CallbackQuery, state: FSMContext):
    book_id = callback.data.split(":")[1]
    await state.update_data(book_id=book_id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎁 Бонусний", callback_data="bid_wallet:bonus"),
            InlineKeyboardButton(text="💰 Звичайний", callback_data="bid_wallet:normal")
        ]
    ])
    await callback.message.edit_text("💳 Оберіть баланс для ставки:", reply_markup=kb)
    await state.set_state(BidState.choosing_balance)

@router.callback_query(BidState.choosing_balance, F.data.startswith("bid_wallet:"))
async def bid_balance(callback: CallbackQuery, state: FSMContext):
    wallet = callback.data.split(":")[1]
    await state.update_data(wallet=wallet)
    await callback.message.edit_text("💰 Введіть суму ставки:")
    await state.set_state(BidState.entering_amount)
@router.message(BidState.entering_amount)
async def process_bid(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    book_id = data["book_id"]
    wallet = data["wallet"]
    user_id = str(message.from_user.id)
    user = users[user_id]
    bid = int(message.text.strip())

    min_bid = auction[book_id]["min_bid"]
    current_bid = auction[book_id]["highest_bid"]

    if bid < min_bid:
        await message.answer(f"❗ Ставка має бути не менше {min_bid} монет.")
        return

    if bid <= current_bid:
        await message.answer(f"❗ Ваша ставка має бути більшою за поточну ({current_bid} монет).")
        return

    if user[wallet] < bid:
        await message.answer("❗ Недостатньо монет.")
        return

    prev_user = auction[book_id]["highest_user"]
    prev_bid = auction[book_id]["highest_bid"]
    prev_wallet = auction[book_id].get("highest_wallet")

    if prev_user == user_id:
        await message.answer("❗ Ви вже є лідером.")
        return

    # Повертаємо монети попередньому
    if prev_user and prev_wallet:
        users[prev_user][prev_wallet] += prev_bid
        await bot.send_message(prev_user, f"⚠️ Вашу ставку перебили в книзі '{book_id}'.")

    # Заморожуємо нову ставку
    user[wallet] -= bid
    auction[book_id]["highest_user"] = user_id
    auction[book_id]["highest_bid"] = bid
    auction[book_id]["highest_wallet"] = wallet

    save_users(users)
    save_auction(auction)

    await message.answer(f"✅ Ваша ставка {bid} монет прийнята!")
    await state.clear()
