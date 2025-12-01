import telebot
from datetime import datetime
import json
import os

# ============================================
# 🌟 Environment Variables للبوت والمطور
BOT_TOKEN = os.getenv("BOT_TOKEN")
DEVELOPER_ID = int(os.getenv("DEV_ID"))
# ============================================

bot = telebot.TeleBot(BOT_TOKEN)

# ------------------------
# حفظ بيانات الأعضاء
# ------------------------
def save_user_to_group_file(group_id, data):
    filename = f"group_{group_id}.json"
    if not os.path.exists(filename):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
    with open(filename, "r+", encoding="utf-8") as f:
        try:
            old = json.load(f)
        except:
            old = []
        old.append(data)
        f.seek(0)
        json.dump(old, f, ensure_ascii=False, indent=2)
        f.truncate()

# ------------------------
# عضو جديد يدخل الجروب
# ------------------------
@bot.message_handler(content_types=['new_chat_members'])
def new_member(msg):
    for user in msg.new_chat_members:
        try:
            bio = bot.get_chat(user.id).bio or "—"
        except:
            bio = "—"

        info = {
            "group_id": msg.chat.id,
            "group_title": msg.chat.title,
            "user_id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name or "",
            "username": user.username or "",
            "bio": bio,
            "joined_at": datetime.utcfromtimestamp(msg.date).strftime("%Y-%m-%d %H:%M:%S UTC")
        }

        save_user_to_group_file(msg.chat.id, info)

        # رسالة جميلة للمطور
        text = (
            f"👤 <b>عضو جديد دخل الجروب!</b>\n\n"
            f"📌 <b>الجروب:</b> {info['group_title']}\n"
            f"👤 <b>الاسم:</b> {info['first_name']} {info['last_name']}\n"
            f"🔗 <b>اليوزر:</b> @{info['username'] if info['username'] else '—'}\n"
            f"🆔 <b>ID:</b> {info['user_id']}\n"
            f"📄 <b>Bio:</b> {info['bio']}\n"
            f"⏰ <b>وقت الانضمام:</b> {info['joined_at']}"
        )

        try:
            bot.send_message(DEVELOPER_ID, text, parse_mode="HTML")
        except:
            print("المطور لم يفتح شات مع البوت.")

        # صورة البروفايل
        try:
            photos = bot.get_user_profile_photos(user.id)
            if photos.total_count > 0:
                file_id = photos.photos[0][0].file_id
                bot.send_photo(DEVELOPER_ID, file_id, caption="📸 Profile Photo")
            else:
                bot.send_message(DEVELOPER_ID, "📸 لا توجد صورة بروفايل.")
        except Exception as e:
            print("Error:", e)

# ------------------------
# لوحة تحكم المطور
# ------------------------
@bot.message_handler(commands=['panel'])
def admin_panel(msg):
    if msg.from_user.id != DEVELOPER_ID:
        return

    keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        telebot.types.InlineKeyboardButton("📊 الإحصائيات", callback_data="stats"),
        telebot.types.InlineKeyboardButton("📄 آخر 10 أعضاء", callback_data="last10"),
        telebot.types.InlineKeyboardButton("📂 المجموعات", callback_data="groups"),
        telebot.types.InlineKeyboardButton("🛠️ إعادة التشغيل", callback_data="restart")
    )

    bot.send_message(DEVELOPER_ID, "⚙️ <b>لوحة تحكم المطور</b>", reply_markup=keyboard, parse_mode="HTML")

# ------------------------
# أزرار لوحة التحكم
# ------------------------
@bot.callback_query_handler(func=lambda c: True)
def panel_actions(c):
    if c.from_user.id != DEVELOPER_ID:
        return

    if c.data == "stats":
        total_users = 0
        groups = 0
        for file in os.listdir():
            if file.startswith("group_") and file.endswith(".json"):
                groups += 1
                with open(file, "r", encoding="utf-8") as f:
                    total_users += len(json.load(f))
        bot.send_message(DEVELOPER_ID, f"📊 <b>الإحصائيات:</b>\n\n👥 الأعضاء المسجلين: {total_users}\n📂 المجموعات: {groups}", parse_mode="HTML")

    elif c.data == "groups":
        groups = [f for f in os.listdir() if f.startswith("group_")]
        txt = "📂 <b>المجموعات المسجلة:</b>\n\n" + "\n".join(groups)
        bot.send_message(DEVELOPER_ID, txt, parse_mode="HTML")

    elif c.data == "last10":
        result = []
        for file in os.listdir():
            if file.startswith("group_"):
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    result.extend(data)
        result = sorted(result, key=lambda x: x["joined_at"], reverse=True)
        last = result[:10]
        msg_text = "📄 <b>آخر 10 أعضاء:</b>\n\n"
        for u in last:
            msg_text += f"- {u['first_name']} ({u['user_id']})\n"
        bot.send_message(DEVELOPER_ID, msg_text, parse_mode="HTML")

    elif c.data == "restart":
        bot.send_message(DEVELOPER_ID, "♻️ جاري إعادة تشغيل البوت...")
        os._exit(0)  # Render سيعيد تشغيل الخدمة تلقائيًا

print("🤖 Bot Running...")
bot.infinity_polling()
