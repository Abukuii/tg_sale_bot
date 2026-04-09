from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import *
from config import *
from database import *
from lessons import *
from keyboards import *

PHONE = 1
ADMIN_BROADCAST = 2


def start(update, context):

    user_id = update.message.from_user.id

    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()

    update.message.reply_text("""
Assalomu alaykum!

Xusniddin Nematov IT Master botiga xush kelibsiz.
Bu bot orqali Excel fayllarni sotib olishingiz mumkin.
""")

    if user is None:

        button = KeyboardButton("📱 Telefon yuborish", request_contact=True)

        update.message.reply_text(
            "Telefon raqamingizni yuboring",
            reply_markup=ReplyKeyboardMarkup([[button]], resize_keyboard=True)
        )

        return PHONE

    else:

        member = context.bot.get_chat_member(CHANNEL, user_id)

        if member.status in ["member", "administrator", "creator"]:

            lessons_button = KeyboardButton("📚 Darslar")

            keyboard = ReplyKeyboardMarkup([[lessons_button]], resize_keyboard=True)

            update.message.reply_text(
                "📚 Darsni tanlang",
                reply_markup=keyboard
            )

        else:

            keyboard = [
                [InlineKeyboardButton("📢 Kanalga obuna", url=f"https://t.me/{CHANNEL.replace('@','')}")],
                [InlineKeyboardButton("✅ Tekshirish", callback_data="check")]
            ]

            update.message.reply_text(
                "Botdan foydalanish uchun kanalga obuna bo'ling",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )


def phone(update, context):

    phone = update.message.contact.phone_number
    user = update.message.from_user

    cursor.execute(
        "INSERT INTO users (user_id,name,phone) VALUES (?,?,?)",
        (user.id, user.first_name, phone)
    )

    conn.commit()

    update.message.reply_text(
        "Telefon raqamingiz tasdiqlandi!",
        reply_markup=ReplyKeyboardRemove()
    )

    keyboard = [
        [InlineKeyboardButton("📢 Kanalga obuna", url=f"https://t.me/{CHANNEL.replace('@','')}")],
        [InlineKeyboardButton("✅ Tekshirish", callback_data="check")]
    ]

    update.message.reply_text(
        "Botdan foydalanish uchun kanalga obuna bo'ling",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return ConversationHandler.END


def show_lessons(update, context):

    update.message.reply_text(
        "📚 Darsni tanlang",
        reply_markup=lessons_menu()
    )


def check(update, context):

    query = update.callback_query
    user_id = query.from_user.id

    lessons_button = KeyboardButton("📚 Darslar")

    keyboard = ReplyKeyboardMarkup([[lessons_button]], resize_keyboard=True)

    member = context.bot.get_chat_member(CHANNEL, user_id)

    if member.status in ["member", "administrator", "creator"]:

        query.message.reply_text(
            "Tabriklaymiz! Siz registratsiyadan o'tdingiz",
            reply_markup=keyboard
        )

        query.message.reply_text(
            "📚 Darsni tanlang",
            reply_markup=lessons_menu()
        )

    else:

        query.answer("Avval kanalga obuna bo'ling", show_alert=True)


def lesson(update, context):

    query = update.callback_query
    data = query.data

    lesson = LESSONS[data]

    context.user_data["lesson"] = data

    text = f"""
📚 {lesson['name']}

💰 Narxi: {lesson['price']}

💳 Karta:
{CARD}

To'lov qilib screenshot yoki pdf yuboring
Admin: {ADMIN}
"""

    query.message.reply_text(text)


def screenshot(update, context):

    user = update.message.from_user
    lesson_key = context.user_data.get("lesson")
    lesson = LESSONS[lesson_key]

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_{user.id}_{lesson_key}"),
            InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{user.id}")
        ]
    ])

    caption = f"""
💰 Yangi to'lov

User: {user.first_name}
ID: {user.id}

Dars: {lesson['name']}
Narxi: {lesson['price']}
"""

    if update.message.photo:

        context.bot.send_photo(
            ADMIN_ID,
            update.message.photo[-1].file_id,
            caption=caption,
            reply_markup=keyboard
        )

    elif update.message.document:

        context.bot.send_document(
            ADMIN_ID,
            update.message.document.file_id,
            caption=caption,
            reply_markup=keyboard
        )

    else:

        update.message.reply_text("❌ Faqat rasm yoki pdf yuboring")
        return

    update.message.reply_text("⏳ To'lov tekshirilmoqda...")


def admin(update, context):

    query = update.callback_query
    query.answer()

    data = query.data.split("_")

    action = data[0]
    user_id = int(data[1])

    if action == "approve":

        lesson_key = data[2]
        lesson = LESSONS[lesson_key]

        cursor.execute(
            "INSERT INTO sales (user_id, lesson) VALUES (?,?)",
            (user_id, lesson_key)
        )

        conn.commit()

        context.bot.send_message(
            user_id,
            "✅ To'lov tasdiqlandi!"
        )

        context.bot.send_document(
            user_id,
            open(lesson["file"], "rb")
        )

        query.edit_message_caption("✅ Tasdiqlandi")

    else:

        context.bot.send_message(
            user_id,
            f"❌ To'lov rad etildi\nAdmin: {ADMIN}"
        )

        query.edit_message_caption("❌ Rad etildi")


# ADMIN PANEL

def admin_panel(update, context):

    if update.message.from_user.id != ADMIN_ID:
        return

    keyboard = [
        ["📊 Statistika", "👥 Foydalanuvchilar"],
        ["🏆 Eng ko'p sotilgan dars"],
        ["📢 Broadcast"]
    ]

    update.message.reply_text(
        "🔐 Admin panel",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )


def stats(update, context):

    if update.message.from_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]

    update.message.reply_text(f"""
📊 BOT STATISTIKASI

👥 Foydalanuvchilar: {users}
🤖 Bot ishlamoqda
""")


def users_count(update, context):

    if update.message.from_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]

    update.message.reply_text(f"👥 Botda {users} ta foydalanuvchi bor")


def top_lessons(update, context):

    if update.message.from_user.id != ADMIN_ID:
        return

    cursor.execute("""
    SELECT lesson, COUNT(*) as total
    FROM sales
    GROUP BY lesson
    ORDER BY total DESC
    """)

    results = cursor.fetchall()

    if not results:
        update.message.reply_text("❌ Hali sotuv yo'q")
        return

    text = "🏆 Eng ko'p sotilgan darslar\n\n"

    for lesson_key, total in results:

        lesson_name = LESSONS[lesson_key]["name"]

        text += f"{lesson_name} — {total} ta\n"

    update.message.reply_text(text)


def broadcast_start(update, context):

    if update.message.from_user.id != ADMIN_ID:
        return

    update.message.reply_text(
        "📢 Barcha foydalanuvchilarga yuboriladigan xabarni yuboring"
    )

    return ADMIN_BROADCAST


def broadcast_send(update, context):

    message = update.message

    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()

    sent = 0

    for user in users:

        user_id = user[0]

        try:

            if message.text:
                context.bot.send_message(user_id, message.text)

            elif message.photo:
                context.bot.send_photo(
                    user_id,
                    message.photo[-1].file_id,
                    caption=message.caption
                )

            elif message.document:
                context.bot.send_document(
                    user_id,
                    message.document.file_id,
                    caption=message.caption
                )

            sent += 1

        except:
            pass

    update.message.reply_text(f"✅ {sent} ta userga yuborildi")

    return ConversationHandler.END


def main():

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PHONE: [MessageHandler(Filters.contact, phone)],
        },
        fallbacks=[]
    )

    broadcast_conv = ConversationHandler(
        entry_points=[MessageHandler(Filters.text("📢 Broadcast"), broadcast_start)],
        states={
            ADMIN_BROADCAST: [
                MessageHandler(
                    Filters.text | Filters.photo | Filters.document,
                    broadcast_send
                )
            ]
        },
        fallbacks=[]
    )

    dp.add_handler(conv)

    dp.add_handler(CommandHandler("admin", admin_panel))

    dp.add_handler(MessageHandler(Filters.text("📚 Darslar"), show_lessons))

    dp.add_handler(MessageHandler(Filters.text("📊 Statistika"), stats))

    dp.add_handler(MessageHandler(Filters.text("👥 Foydalanuvchilar"), users_count))

    dp.add_handler(MessageHandler(Filters.text("🏆 Eng ko'p sotilgan dars"), top_lessons))

    dp.add_handler(CallbackQueryHandler(check, pattern="check"))

    dp.add_handler(CallbackQueryHandler(lesson, pattern="lesson"))

    dp.add_handler(MessageHandler(Filters.photo | Filters.document, screenshot))

    dp.add_handler(CallbackQueryHandler(admin, pattern="approve|reject"))

    dp.add_handler(broadcast_conv)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()