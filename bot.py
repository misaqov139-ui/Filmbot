 import sqlite3
import telebot
from telebot import types

TOKEN = "9165959275:AAFpoEr3CsQpp36xjdEjw9fVu26NL1wakuo"
ADMIN_ID = 7630210071

CHANNEL_ID = "@oltinkadr_uz"
CHANNEL_URL = "https://t.me/oltinkadr_uz"

bot = telebot.TeleBot(TOKEN)

# --- SQLite baza ---
conn = sqlite3.connect("films.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS films (
    code TEXT PRIMARY KEY,
    file_id TEXT,
    caption TEXT
)
""")
conn.commit()

admin_states = {}


# --- Majburiy obuna tekshiruvi ---
def is_subscribed(user_id):
    if user_id == ADMIN_ID:
        return True
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["creator", "administrator", "member"]
    except Exception:
        return False


def send_sub_message(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_join = types.InlineKeyboardButton(
        "Kanalga a'zo bo'lish",
        url=CHANNEL_URL
    )
    btn_check = types.InlineKeyboardButton(
        "Obunani tekshirish",
        callback_data="check_sub"
    )
    markup.add(btn_join, btn_check)

    bot.send_message(
        chat_id,
        f"Filmlarni ko'rish uchun avval quyidagi kanalga a'zo bo'ling:\n{CHANNEL_URL}",
        reply_markup=markup
    )


def send_main_menu(message):
    text = (
        "Assalomu alaykum!\n"
        "Kerakli kino kodini yuboring (masalan: 101) — men sizga yuboraman."
    )
    if message.from_user.id == ADMIN_ID:
        text += "\n\nAdmin menyusi:\n/addfilm — yangi kino qo'shish"
    bot.send_message(message.chat.id, text)


# --- /start ---
@bot.message_handler(commands=["start"])
def handle_start(message):
    if not is_subscribed(message.from_user.id):
        send_sub_message(message.chat.id)
        return
    send_main_menu(message)


# --- Obunani tekshirish tugmasi ---
@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def callback_check_sub(call):
    if is_subscribed(call.from_user.id):
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        bot.answer_callback_query(call.id, "Obuna tasdiqlandi!")
        send_main_menu(call.message)
    else:
        bot.answer_callback_query(
            call.id,
            "Siz hali kanalga a'zo bo'lmagansiz!",
            show_alert=True
        )


# --- Admin: /addfilm ---
@bot.message_handler(commands=["addfilm"])
def handle_addfilm(message):
    if message.from_user.id != ADMIN_ID:
        return
    admin_states[message.from_user.id] = {"step": "code"}
    bot.send_message(message.chat.id, "Yangi kino uchun kod kiriting (masalan: 101):")


@bot.message_handler(func=lambda m: m.from_user.id in admin_states)
def handle_admin_steps(message):
    user_id = message.from_user.id
    state = admin_states[user_id]

    if state["step"] == "code":
        code = message.text.strip()
        state["code"] = code
        state["step"] = "video"
        bot.send_message(message.chat.id, "Endi kino videosini yuboring:")
    elif state["step"] == "video":
        if not message.video:
            bot.send_message(message.chat.id, "Iltimos, video fayl yuboring!")
            return
        file_id = message.video.file_id
        caption = message.caption or f"Kino kodi: {state['code']}"
        cursor.execute(
            "INSERT OR REPLACE INTO films (code, file_id, caption) VALUES (?, ?, ?)",
            (state["code"], file_id, caption)
        )
        conn.commit()
        del admin_states[user_id]
        bot.send_message(message.chat.id, f"Kino saqlandi! Kod: {state['code']}")


# --- Kino kodini qidirish ---
@bot.message_handler(func=lambda m: True)
def handle_film_code(message):
    if not is_subscribed(message.from_user.id):
        send_sub_message(message.chat.id)
        return

    code = (message.text or "").strip()
    cursor.execute("SELECT file_id, caption FROM films WHERE code = ?", (code,))
    row = cursor.fetchone()

    if row:
        file_id, caption = row
        bot.send_video(message.chat.id, file_id, caption=caption)
    else:
        bot.send_message(message.chat.id, "Bunday kodli kino topilmadi.")


print("Bot ishga tushdi...")
bot.infinity_polling(none_stop=True)



