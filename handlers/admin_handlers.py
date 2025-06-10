from aiogram import Router, types, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from data.auction_data import auction, save_auction
from database import load_users, save_users
from config import ADMINS
from handlers.data.utils.storage import users
from datetime import datetime
router = Router()

def is_admin(user_id: int | str) -> bool:
  return str(user_id) in ADMINS

### --- Callbacks --- ###

@router.callback_query(F.data.startswith("accept:"))
async def accept_withdrawal(callback: CallbackQuery):
            parts = callback.data.split(":")
            user_id, amount = parts[1], int(parts[2])
            user = users.get(user_id)

            if not user:
                await callback.message.answer("❌ Користувача не знайдено.")
                return

            # 🔐 Перевірка на дубль
            if user.get("last_withdrawal") != amount:
                await callback.message.answer("⚠️ Цю заявку вже оброблено.")
                return

            # Знімаємо заявку
            user["last_withdrawal"] = None
            now = datetime.now().strftime("%d.%m.%Y")
            user["history"].append(f"💵 {now} | зняття: {amount} монет")
            save_users(users)

            await callback.message.edit_text(f"✅ Заявка на вивід {amount} монет для ID {user_id} підтверджена.")
            try:
                await callback.bot.send_message(int(user_id), f"✅ Ваш запит на зняття {amount} монет підтверджено модератором.Гроші надійдуть до вас протягом 15 робочих днів — залишається трохи почекати.")
            except:
                pass


@router.callback_query(F.data.startswith("decline:"))
async def decline_withdrawal(callback: CallbackQuery):
            parts = callback.data.split(":")
            user_id, amount = parts[1], int(parts[2])
            user = users.get(user_id)

            if not user:
                await callback.message.answer("❌ Користувача не знайдено.")
                return

            # 🔐 Перевірка на дубль
            if user.get("last_withdrawal") != amount:
                await callback.message.answer("⚠️ Цю заявку вже оброблено.")
                return

            # Скасовуємо заявку, повертаємо монети
            user["normal"] += amount
            user["last_withdrawal"] = None
            user["history"].append(f"❌ Відхилено зняття: {amount} монет")
            save_users(users)

            await callback.message.edit_text(f"❌ Заявка на вивід {amount} монет для ID {user_id} відхилена. Монети повернено.")
            try:
                await callback.bot.send_message(
                    int(user_id),
                    f"❌ Ваш запит на зняття {amount} монет було відхилено.\n💰 Монети повернуто на баланс."
                )
            except:
                pass


### --- Адмін-команди --- ###

@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ А ти шалун!.")
        return

    await message.answer(
        "🔧 Панель адміністратора:\n\n"
        "📋 Список доступних команд:\n"
        "/give_bonus user_id сума – видати бонусні монети\n"
        "/give_normal user_id сума – видати звичайні монети\n"
        "/take_bonus user_id сума – забрати бонусні монети\n"
        "/take_normal user_id сума – забрати звичайні монети\n"
        "/user_balance user_id – переглянути баланс\n"
        "/ban user_id – заблокувати користувача\n"
        "/unban user_id – розблокувати користувача\n"
        "/list_banned – список забанених\n"
        "/add_auction book_id опис – додати аукціон\n"
        "/remove_auction book_id – видалити аукціон\n"
        "/create_auction book_id мін_ставка опис – створити аукціон\n"
        "/finish_auction book_id – завершити аукціон\n"
        "/users – список користувачі\n"
        "/reset_all – очистити всі дані\n"
    )

@router.message(Command("give_bonus"))
async def give_bonus(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("🚫 ШАХРАЙ !!!.") 
        return
    try:
        _, user_id, amount = message.text.split()
        users[user_id]["bonus"] += int(amount)
        save_users(users)
        await message.answer(f"✅ Видано {amount} бонусних монет користувачу {user_id}")
    except:
        await message.answer("❌ Невірний формат. /give_bonus user_id сума")

@router.message(Command("give_normal"))
async def give_normal(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("🚫 ШАХРАЙ !!!.") 
        return
    try:
        _, user_id, amount = message.text.split()
        users[user_id]["normal"] += int(amount)
        save_users(users)
        await message.answer(f"✅ Видано {amount} звичайних монет користувачу {user_id}")
    except:
        await message.answer("❌ Невірний формат. /give_normal user_id сума")

@router.message(Command("take_bonus"))
async def take_bonus(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("🚫 ШАХРАЙ !!!.") 
        return
    try:
        _, user_id, amount = message.text.split()
        users[user_id]["bonus"] -= int(amount)
        save_users(users)
        await message.answer(f"✅ Забрано {amount} бонусних монет у {user_id}")
    except:
        await message.answer("❌ Помилка.")

@router.message(Command("take_normal"))
async def take_normal(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("🚫 ШАХРАЙ !!!.") 
        return
    try:
        _, user_id, amount = message.text.split()
        users[user_id]["normal"] -= int(amount)
        save_users(users)
        await message.answer(f"✅ Забрано {amount} звичайних монет у {user_id}")
    except:
        await message.answer("❌ Помилка.")

@router.message(Command("user_balance"))
async def user_balance(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("🚫 ШАХРАЙ !!!.") 
        return
    try:
        _, user_id = message.text.split()
        u = users[user_id]
        await message.answer(f"👤 ID: {user_id}\nПозивний: {u['nickname']}\n🎁 Бонус: {u['bonus']}\n💰 Звичайні: {u['normal']}")
    except:
        await message.answer("❌ Користувача не знайдено.")

@router.message(Command("ban"))
async def ban_user(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("🚫 ШАХРАЙ !!!.") 
        return
    try:
        _, user_id = message.text.split()
        users[user_id]["banned"] = True
        save_users(users)
        await message.answer(f"🚫 Користувача {user_id} заблоковано.")
    except:
        await message.answer("❌ Помилка.")

@router.message(Command("unban"))
async def unban_user(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("🚫 ШАХРАЙ !!!.") 
        return
    try:
        _, user_id = message.text.split()
        users[user_id]["banned"] = False
        save_users(users)
        await message.answer(f"✅ Користувача {user_id} розблоковано.")
    except:
        await message.answer("❌ Помилка.")

@router.message(Command("list_banned"))
async def list_banned(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ ШАХРАЙ!.")
        return
    banned = [f"{uid} - {u['nickname']}" for uid, u in users.items() if u.get("banned")]
    if not banned:
        await message.answer("✅ Немає заблокованих користувачів.")
    else:
        await message.answer("🚫 Заблоковані користувачі:\n" + "\n".join(banned))

### --- Аукціони --- ###

@router.message(Command("create_auction"))
async def create_auction(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ ШАХРАЙ!.")
        return

    try:
        _, book_id, min_bid, *desc = message.text.split()
        description = " ".join(desc)
        auction[book_id] = {
            "description": description,
            "highest_bid": 0,
            "highest_user": None,
            "min_bid": int(min_bid),
            "highest_wallet": None
        }
        save_auction(auction)
        await message.answer(f"✅ Аукціон '{book_id}' створено з мінімальною ставкою {min_bid}")
    except:
        await message.answer("❗ Формат: /create_auction <book_id> <min_bid> <опис>")

@router.message(Command("add_auction"))
async def add_auction_book(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ ШАХРАЙ!.")
        return
    try:
        _, book_id, *desc = message.text.split()
        description = " ".join(desc)
        if book_id in auction:
            await message.answer("❗ Ця книга вже в аукціоні.")
            return
        auction[book_id] = {
            "description": description,
            "min_bid": 200,
            "highest_bid": 0,
            "highest_user": None,
            "frozen": {}
        }
        save_auction(auction)
        await message.answer(f"✅ Додано книгу {book_id} до аукціону.")
    except:
        await message.answer("❌ Формат: /add_auction book_id опис")

@router.message(Command("remove_auction"))
async def remove_auction_book(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ ШАХРАЙ!.")
        return
    try:
        _, book_id = message.text.split()
        if book_id in auction:
            auction.pop(book_id)
            save_auction(auction)
            await message.answer(f"🗑 Книга {book_id} видалена з аукціону.")
        else:
            await message.answer("❗ Книга не знайдена.")
    except:
        await message.answer("❌ Формат: /remove_auction book_id")

@router.message(Command("finish_auction"))
async def finish_auction(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ ШАХРАЙ!.")
        return
    bot = message.bot
    parts = message.text.strip().split()

    if len(parts) != 2:
        await message.answer("❗ Використання: /finish_auction <book_id>")
        return

    book_id = parts[1]

    if book_id not in auction:
        await message.answer("❌ Аукціон з таким ID не знайдено.")
        return

    data = auction.pop(book_id)
    save_auction(auction)

    bid = data['highest_bid']
    winner_id = data['highest_user']
    book_desc = data.get('description', "—")

    if winner_id:
        nickname = users.get(winner_id, {}).get("nickname", "Невідомий")
        try:
            await bot.send_message(
                winner_id,
                f"🎉 Ви виграли аукціон на книгу '{book_id}'!\n"
                f"📖 Опис: {book_desc}\n"
                f"💰 Ставка: {bid} монет"
            )
        except:
            pass

        for admin_id in ADMINS:
            await bot.send_message(
                admin_id,
                f"🏁 Аукціон завершено!\n"
                f"📚 Книга: {book_id}\n"
                f"📄 Опис: {book_desc}\n"
                f"👤 Переможець: {nickname} (ID: {winner_id})\n"
                f"💰 Ставка: {bid} монет"
            )

        await message.answer("✅ Аукціон завершено. Переможця сповіщено.")
    else:
        for admin_id in ADMINS:
            await bot.send_message(
                admin_id,
                f"⚠️ Аукціон '{book_id}' завершено без переможця."
            )
        await message.answer("⚠️ Аукціон завершено. Не було ставок.")

@router.message(Command("auction_list"))
async def list_auctions(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ ШАХРАЙ!.")
        return
    if not auction:
        await message.answer("📚 Активних аукціонів немає.")
        return

    result = "📚 Активні аукціони:\n"
    for book_id in auction:
        result += f"• {book_id}\n"
    await message.answer(result)

@router.message(Command("reset_all"))
async def reset_all_data(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ ШАХРАЙ!.")
        return

    users.clear()
    save_users(users)
    auction.clear()
    save_auction(auction)
    await message.answer("♻️ Усі дані очищено. Бот починає з чистого аркуша.")
@router.message(Command("users"))
async def show_users(message: Message):
        if not is_admin(message.from_user.id):
            return await message.answer("⛔ У вас немає доступу до цієї команди.")

        if not users:
            return await message.answer("Поки що немає зареєстрованих користувачів.")

        users_list = "\n\n".join([
            f"🆔 ID: {uid}\n"
            f"📛 Позивний: {u.get('nickname', 'не вказано')}"
            for uid, u in users.items()
        ])

        await message.answer(f"👥 Учасники бота:\n\n{users_list}")

