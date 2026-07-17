import sqlite3
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import requests

# --- БАПТАУЛАР ---
API_KEY = "0074455f628575a0f0a1650e42e12d1a"
API_URL = "https://topsmm.uz/api/v2"
BOT_TOKEN = "8760840819:AAGjJVBOM2JBK0RS7q9pQRFrea1myWTb0wU"
ADMIN_ID = 123456789  # ӨЗ ID-ІҢДІ ЖАЗ

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# --- ДЕРЕКҚОР ---
conn = sqlite3.connect('bot_data.db')
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, balance REAL)')
conn.commit()

class AdminStates(StatesGroup):
    waiting_for_balance = State()

# --- ФУНКЦИЯЛАР ---
def get_main_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("💰 Балансым", callback_data="check_bal"),
           types.InlineKeyboardButton("💳 Толтыру (Kaspi)", callback_data="deposit"))
    kb.add(types.InlineKeyboardButton("🚀 TikTok Накрутка", callback_data="smm_tiktok"),
           types.InlineKeyboardButton("✈️ Telegram Накрутка", callback_data="smm_tg"))
    return kb

# --- КОМАНДАЛАР ---
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user_id = message.from_user.id
    cursor.execute('INSERT OR IGNORE INTO users VALUES (?, ?)', (user_id, 0))
    conn.commit()
    
    args = message.get_args()
    if args and args.isdigit():
        inviter = int(args)
        cursor.execute('UPDATE users SET balance = balance + 20 WHERE id = ?', (inviter,))
        conn.commit()
        await bot.send_message(inviter, "🎉 Сіздің рефералыңыз тіркелді! Балансқа +20 тг қосылды.")
    
    await message.answer("Сәлем! Ботқа қош келдің.", reply_markup=get_main_keyboard())

# --- АДМИН ПАНЕЛЬ ---
@dp.message_handler(commands=['admin'])
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Админ: ID және сумманы жаз (мысалы: 12345 500 немесе 12345 -100)")
        await AdminStates.waiting_for_balance.set()

@dp.message_handler(state=AdminStates.waiting_for_balance)
async def process_admin_balance(message: types.Message, state: FSMContext):
    try:
        user_id, amount = message.text.split()
        cursor.execute('UPDATE users SET balance = balance + ? WHERE id = ?', (float(amount), int(user_id)))
        conn.commit()
        await message.answer(f"✅ Пайдаланушы {user_id} балансы {amount}-ға өзгерді.")
    except:
        await message.answer("❌ Қате! Дұрыс формат: 12345 500")
    await state.finish()

# --- CALLBACK (КНОПКАЛАР) ---
@dp.callback_query_handler(lambda c: c.data == 'check_bal')
async def check_bal(c: types.CallbackQuery):
    cursor.execute('SELECT balance FROM users WHERE id = ?', (c.from_user.id,))
    bal = cursor.fetchone()[0]
    await c.answer(f"Сіздің балансыңыз: {bal} тг")

@dp.callback_query_handler(lambda c: c.data == 'deposit')
async def deposit(c: types.CallbackQuery):
    await c.message.answer("💳 Kaspi аударым: 77471164091 (Аббос)")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
