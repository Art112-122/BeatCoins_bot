import asyncio
import logging
import sys
import os
import aiomysql
from aiogram.fsm.context import FSMContext
from api.api import get_binance_price

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types.bot_command import BotCommand
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from bot.state import State_settings
from db.connection import get_mysql_connection, create_tables

load_dotenv()

TOKEN = os.environ.get("BOT_TOKEN")

WEB_APP = os.environ.get("WEB_APP")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

dp = Dispatcher()

BOT_START_COMMAND = BotCommand(command="start", description="Стартове меню")


async def get_main_keyboard(message):
    connection = await get_mysql_connection()
    cursor: aiomysql.Cursor = await connection.cursor()
    await cursor.execute(
        """
        SELECT notices FROM users WHERE user_id = %s;
        """,
        (message.from_user.id,)
    )
    notice = await cursor.fetchone()
    if not notice[0]:
        keyboard_basic = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Налаштування⚙"), KeyboardButton(text='Показати графік📈')],
                [KeyboardButton(text="Показати курс💰"), KeyboardButton(text='Увімкнути повідомлення🔊')]
            ],
            resize_keyboard=True,
            one_time_keyboard=False
        )
        return keyboard_basic
    keyboard_basic = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Налаштування⚙"), KeyboardButton(text='Показати графік📈')],
            [KeyboardButton(text="Показати курс💰"), KeyboardButton(text='Вимкнути повідомлення🔈')]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard_basic


keyboard_setting = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text="💸Монета"
            )
        ],
        [
            KeyboardButton(
                text="📉Нижний ліміт"
            )
        ],
        [

            KeyboardButton(
                text="📈Вищий ліміт"
            )
        ],
        [
            KeyboardButton(
                text="↩Повернутися в головне меню"
            )
        ]
    ]

)


async def settings(message):
    connection = await get_mysql_connection()
    cursor: aiomysql.Cursor = await connection.cursor()
    await cursor.execute(
        """
        SELECT token, low_limit, high_limit FROM users WHERE user_id = %s;
        """,
        (message.from_user.id,)
    )
    answer = await cursor.fetchone()
    if isinstance(answer, tuple):
        await message.answer("Отже, <b>ваші налаштування</b>:\n"
                             f"💸Монета: <b>{answer[0]}</b>\n"
                             f"Повідомити коли <b>{answer[0]}</b>:\n"
                             f"Опустится ниже <b>{answer[1]}$</b>\n"
                             f"Зросте вище <b>{answer[2]}$</b>\n"
                             f"Що хочеш редагувати?🔄", reply_markup=keyboard_setting)


async def price_checker():
    global answer

    while True:
        try:
            connection = await get_mysql_connection()
            cursor = await connection.cursor(aiomysql.DictCursor)

            await cursor.execute("""
                SELECT user_id, token, low_limit, high_limit, notices 
                FROM users
            """)
            users = await cursor.fetchall()

            for user in users:
                if user["notices"]:


                    user_id = user["user_id"]
                    token = user["token"]
                    low_limit = user["low_limit"]
                    high_limit = user["high_limit"]

                    if low_limit is None or high_limit is None:
                        continue

                    price_data = await get_binance_price(token)
                    if price_data is None:
                        continue
                    price = price_data[0]

                    if price >= high_limit:
                        answer = await bot.send_message(
                            user_id,
                            f"📈 <b>{token}</b> перевищив верхній ліміт: {price:.2f} USDT!"
                        )
                        await asyncio.sleep(60)
                        await bot.delete_message(chat_id=answer.chat.id, message_id=answer.message_id)

                    elif price <= low_limit:
                        answer = await bot.send_message(
                            user_id,
                            f"📉 <b>{token}</b> опустився нижче нижнього ліміту: {price:.2f} USDT!"
                        )
                        await asyncio.sleep(60)
                        await bot.delete_message(chat_id=answer.chat.id, message_id=answer.message_id)

            await asyncio.sleep(60)

        except Exception as e:
            logging.error(f"[price_checker error] {e}")
            await asyncio.sleep(10)


@dp.message(F.text == "Показати курс💰")
async def coin_handler(message: Message):
    connection = await get_mysql_connection()
    cursor: aiomysql.Cursor = await connection.cursor()
    await cursor.execute(
        """
        SELECT token FROM users WHERE user_id = %s;
        """,
        (message.from_user.id,)
    )
    symbol = await cursor.fetchone()
    price, percent = await get_binance_price(symbol[0])
    await message.answer(f"💰 {symbol[0]}: {price:.2f} USD ({percent:+.2f}%)")


@dp.message(F.text == "Налаштування⚙")
async def setting_handler(message: Message):
    try:
        await settings(message)
    except aiomysql.Error as e:
        await message.answer("Щось пішло не так🤒")
        raise e


@dp.message(F.text == "💸Монета")
async def token_handler(message: Message, state: FSMContext):
    await state.set_state(State_settings.token)
    tokens = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT', 'DOGEUSDT', 'ADAUSDT', 'DOTUSDT', 'AVAXUSDT',
              'LINKUSDT']
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=tokens[0]), KeyboardButton(text=tokens[1]), KeyboardButton(text=tokens[2])],
                  [KeyboardButton(text=tokens[3]), KeyboardButton(text=tokens[4]), KeyboardButton(text=tokens[5])],
                  [KeyboardButton(text=tokens[6]), KeyboardButton(text=tokens[7]), KeyboardButton(text=tokens[8])],
                  [KeyboardButton(text=tokens[9])]])
    await message.answer('Обери на що хочеш змінити💸', reply_markup=keyboard)


@dp.message(F.text == "📉Нижний ліміт")
async def low_limit_handler(message: Message, state: FSMContext):
    await state.set_state(State_settings.low)
    await message.answer('Введіть новий ліміт до попередження', reply_markup=ReplyKeyboardRemove())


@dp.message(F.text == "📈Вищий ліміт")
async def high_limit_handler(message: Message, state: FSMContext):
    await state.set_state(State_settings.high)
    await message.answer('Введіть новий ліміт до попередження', reply_markup=ReplyKeyboardRemove())


@dp.message(State_settings.high)
async def low_handler(message: Message, state: FSMContext):
    try:
        ms = int(message.text)
        connection = await get_mysql_connection()
        cursor: aiomysql.Cursor = await connection.cursor()
        await cursor.execute(
            """
            UPDATE users
            SET high_limit = %s
            WHERE user_id = %s;
            """,
            (ms, message.from_user.id)
        )
        await connection.commit()
        await state.clear()
        await message.answer("Ліміт змінений🔄")
        await settings(message)
    except aiomysql.Error as e:
        await message.answer("Щось пішло не так🤒")
        raise e
    except ValueError:
        await message.answer("<b>Введіть ціле число</b>")


@dp.message(State_settings.low)
async def low_handler(message: Message, state: FSMContext):
    try:
        ms = int(message.text)
        connection = await get_mysql_connection()
        cursor: aiomysql.Cursor = await connection.cursor()
        await cursor.execute(
            """
            UPDATE users
            SET low_limit = %s
            WHERE user_id = %s;
            """,
            (ms, message.from_user.id)
        )
        await connection.commit()
        await state.clear()
        await message.answer("Ліміт змінений🔄")
        await settings(message)
    except aiomysql.Error as e:
        await message.answer("Щось пішло не так🤒")
        raise e
    except ValueError:
        await message.answer("<b>Введіть ціле число</b>")


@dp.message(State_settings.token)
async def state_token_handler(message: Message, state: FSMContext):
    try:
        ms = message.text
        tokens = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT', 'DOGEUSDT', 'ADAUSDT', 'DOTUSDT', 'AVAXUSDT',
                  'LINKUSDT']
        if ms in tokens:
            connection = await get_mysql_connection()
            cursor: aiomysql.Cursor = await connection.cursor()
            await cursor.execute(
                """
                UPDATE users
                SET token = %s
                WHERE user_id = %s;
                """,
                (ms, message.from_user.id)
            )
            await connection.commit()
            await state.clear()
            await message.answer("Монета змінена🔄")
            await settings(message)
    except aiomysql.Error as e:
        await message.answer("Щось пішло не так🤒")
        raise e


@dp.message(F.text == "Показати графік📈")
async def chart_handler(message: Message):
    connection = await get_mysql_connection()
    cursor: aiomysql.Cursor = await connection.cursor()
    await cursor.execute(
        """
        SELECT token FROM users WHERE user_id = %s;
        """,
        (message.from_user.id,)
    )
    symbol = await cursor.fetchone()
    full_url = f"{WEB_APP}?symbol=BINANCE:{symbol[0]}"

    keyboard_chart = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📈 Відкрити графік",
                    web_app=WebAppInfo(url=full_url)
                )
            ]
        ]
    )

    await message.answer(f"Графік для <b>{symbol[0]}</b>", reply_markup=keyboard_chart)


@dp.message(F.text == "↩Повернутися в головне меню")
async def return_handler(message: Message):
    keyboard_basic = await get_main_keyboard(message)
    await message.answer("Повернення в головне меню↩", reply_markup=keyboard_basic)


@dp.message(F.text.in_(["Вимкнути повідомлення🔈", "Увімкнути повідомлення🔊"]))
async def notice_handler(message: Message):
    connection = await get_mysql_connection()
    cursor: aiomysql.Cursor = await connection.cursor()
    await cursor.execute(
        "SELECT notices FROM users WHERE user_id = %s;",
        (message.from_user.id,)
    )
    result = await cursor.fetchone()

    current_notice = bool(result[0])
    new_notice = not current_notice

    await cursor.execute(
        """
        UPDATE users
        SET notices = %s
        WHERE user_id = %s;
        """,
        (new_notice, message.from_user.id)
    )
    await connection.commit()

    keyboard = await get_main_keyboard(message)
    if new_notice:
        await message.answer("Повідомлення увімкнені🔊", reply_markup=keyboard)
    else:
        await message.answer("Повідомлення вимкнені🔈", reply_markup=keyboard)


@dp.message(CommandStart)
async def start(message: Message) -> None:
    try:
        connection = await get_mysql_connection()
        cursor: aiomysql.Cursor = await connection.cursor()
        await cursor.execute("""
            SELECT id FROM users WHERE user_id = %s;
        """, (message.from_user.id,))
        check = await cursor.fetchone()
        if not isinstance(check, tuple):
            await cursor.execute(
                """INSERT INTO users (user_id, name, token, notices)
                VALUES (%s, %s, 'BTCUSDT', TRUE)
                """,
                (message.from_user.id, message.from_user.full_name))
            await connection.commit()
    except aiomysql.Error as e:
        raise e
    keyboard_basic = await get_main_keyboard(message)
    await message.answer(
        f'''👋 <b>Привіт!</b> Я — твій <b>крипто-бот асистент</b> 📊

Я допоможу тобі:
• Переглядати графіки з <b>TradingView</b> 🔎  
• Відстежувати актуальні курси криптовалют 💰  
• Швидко дізнаватись про взліти та падіння 🚀  

<b>Готовий почати?</b> Обери монету та дивись графік прямо зараз ⤵️''', reply_markup=keyboard_basic)


async def main() -> None:
    await bot.set_my_commands([BOT_START_COMMAND])
    await create_tables()
    asyncio.create_task(price_checker())
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
