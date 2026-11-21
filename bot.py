import sqlite3
import telebot
from telebot import types

TOKEN = "9165959275:AAFpoEr3CsQpp36xjdEjw9fVu26NL1wakuo
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
    btn_join = types.InlineKeyboardButton("🎬 @oltinkadr_uz kanaliga a'zo bo'lish", url=CHANNEL_URL)[span_3](start_span)[span_3](end_span)
    btn_check = types.InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_sub")
    markup.add(btn_join, btn_check)

    bot.send_message(
        chat_id,
        "Filmlarni ko‘rish uchun avval quyidagi kanalga a'zo bo‘ling:\n"
        f"{CHANNEL_URL}",[span_4](start_span)[span_4](end_span)
        reply_markup=markup
    )


def send_main_menu(message):
    text = (
        "Assalomu alaykum!\n"
        "Kerakli kino kodini yuboring (masalan: 101) — men sizga yuboraman.[span_5](start_span)"[span_5](end_span)
    )
    if message.from_user.id == ADMIN_ID:
        text += "\n\n🛠 Admin menyusi:\n/addfilm — yangi kino qo‘shish[span_6](start_span)"[span_6](end_span)
    bot.send_message(message.chat.id, text)


# --- /start ---
@bot.message_handler(commands=["start"])
def handle_start(message):
    if not is_subscribed(message.from_user.id):
        send_sub_message(message.chat.id)
        return
    send_main_menu(message)


# --- Tekshirish tugmasi ---
@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def callback_check_sub(call):
    if is_subscribed(call.from_user.id):
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        bot.answer_callback_query(call.id, "Tasdiqlandi! Marhamat.")
        send_main_menu(call.message)
    else:
        bot.answer_callback_query(
            call.id,
            "Hali kanalga a'zo emassiz! Avval a'zo bo‘lib, keyin bosing.",
            show_alert=True
        )


# --- Admin: /addfilm ---
admin_states = {}


@bot.message_handler(commands=["addfilm"])
def handle_addfilm(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "Bu buyruq faqat admin uchun.")
        return
    admin_states[message.from_user.id] = {"step": "code"}
    bot.send_message(message.chat.id, "Yangi kino kodini kiriting (masalan: 101):")[span_7](start_span)[span_7](end_span)


@bot.message_handler(func=lambda m: m.from_user.id in admin_states)
def handle_admin_steps(message):
    user_id = message.from_user.id
    state = admin_states[user_id]

    if state["step"] == "code":
        code = (message.text or "").strip()
        if not code:
            bot.send_message(message.chat.id, "Kod bo‘sh bo‘lmasin, qaytadan yozing:")
            return
        state["code"] = code
        state["step"] = "video"
        bot.send_message(message.chat.id, f"Kod `{code}` saqlandi. Endi kino videosini yuboring:", parse_mode="Markdown")

    elif state["step"] == "video":
        if not message.video:
            bot.send_message(message.chat.id, "Faqat video fayl yuboring.")
            return
        file_id = message.video.file_id
        caption = message.caption or f"🎬 Kod: {state['code']}\nKanalimiz: {CHANNEL_URL}[span_8](start_span)"[span_8](end_span)
        cursor.execute(
            "INSERT OR REPLACE INTO films (code, file_id, caption) VALUES (?, ?, ?)",
            (state["code"], file_id, caption)
        )
        conn.commit()
        del admin_states[user_id]
        bot.send_message(message.chat.id, f"✅ Tayyor! Kino `{state['code']}` kodi bilan bazaga qo‘shildi.", parse_mode="Markdown")


# --- Kino kodini qidirish ---
@bot.message_handler(func=lambda m: True)
def handle_film_request(message):
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
        bot.send_message(message.chat.id, "Kechirasiz, bu kod bo‘yicha kino topilmadi. Boshqa kod yuboring.")


if __name__ == "__main__":
    print("Bot ishga tushdi...")
    bot.infinity_polling(none_stop=True)


