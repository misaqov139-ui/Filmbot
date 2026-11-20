import os
import sqlite3
import telebot
from telebot import types

# Token va majburiy kanalni o'zingiznikiga almashtiring
TOKEN = os.getenv("BOT_TOKEN", "BU_YERGA_BOT_TOKEN_YOZING")
ADMIN_ID = 123456789  # O'zingizning Telegram ID raqamingiz
CHANNEL_USERNAME = "@kanal_username"  # Majburiy obuna kanali (@ bilan)

bot = telebot.TeleBot(TOKEN)

# SQLite bazani ulash va jadvallarni yaratish
conn = sqlite3.connect("filmbot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    status TEXT DEFAULT 'user'
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS movies (
    code TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    file_id TEXT NOT NULL
)
""")
conn.commit()


def is_subscribed(user_id: int) -> bool:
    """Foydalanuvchi majburiy kanalga obuna bo'lganini tekshiradi."""
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception:
        return False


def send_subscribe_prompt(chat_id: int):
    """Obuna bo'lish tugmalari bilan xabar yuboradi."""
    clean_channel = CHANNEL_USERNAME.lstrip("@")
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            "📢 Kanalga obuna bo‘lish",
            url=f"https://t.me/{clean_channel}"
        )
    )
    markup.add(
        types.InlineKeyboardButton(
            "✅ Tekshirish",
            callback_data="check_sub"
        )
    )
    bot.send_message(
        chat_id,
        "🔒 Davom etish uchun quyidagi kanalga obuna bo‘ling:",
        reply_markup=markup
    )


@bot.message_handler(commands=["start"])
def handle_start(message):
    user_id = message.from_user.id
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()

    if not is_subscribed(user_id):
        send_subscribe_prompt(message.chat.id)
        return

    bot.send_message(
        message.chat.id,
        "🎬 <b>Filmbot</b>ga xush kelibsiz!\n\n"
        "Kerakli film kodini yuboring (masalan: <code>101</code>).",
        parse_mode="HTML"
    )


@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def handle_check_sub(call):
    if is_subscribed(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Obuna tasdiqlandi!")
        bot.edit_message_text(
            "🎉 Rahmat! Endi film kodini yuborishingiz mumkin.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )
    else:
        bot.answer_callback_query(
            call.id,
            "❌ Hali obuna bo‘lmadingiz!",
            show_alert=True
        )


@bot.message_handler(func=lambda message: True)
def handle_movie_code(message):
    user_id = message.from_user.id
    if not is_subscribed(user_id):
        send_subscribe_prompt(message.chat.id)
        return

    code = (message.text or "").strip()
    cursor.execute(
        "SELECT title, description, file_id FROM movies WHERE code = ?",
        (code,)
    )
    movie = cursor.fetchone()

    if not movie:
        bot.send_message(
            message.chat.id,
            "❌ Bunday kod bilan film topilmadi. Boshqa kod kiriting."
        )
        return

    title, description, file_id = movie
    caption = f"🎥 <b>{title}</b>"
    if description:
        caption += f"\n\n📝 {description}"

    bot.send_video(
        message.chat.id,
        file_id,
        caption=caption,
        parse_mode="HTML"
    )


if __name__ == "__main__":
    print("Filmbot ishga tushdi...")
    bot.infinity_polling(skip_pending=True)
