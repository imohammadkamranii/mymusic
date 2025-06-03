import os
import json
from telebot import TeleBot
from github import Github

# ============================
# تنظیمات اولیه
# ============================

# دریافت توکن‌ها از متغیرهای محیطی
BOT_TOKEN = "7693573912:AAH5GlCeMvYolHuq8BckIEKgbDogcg6sldM" # توکن ربات تلگرام
GITHUB_TOKEN = "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"  # توکن گیت‌هاب
REPO_NAME = "imohammadkamranii/mymusic" # نام مخزن گیت‌هاب
JSON_FILE_PATH = "playlist.json"  # مسیر فایل JSON در مخزن

# ایجاد شیء ربات تلگرام و گیت‌هاب
bot = TeleBot(BOT_TOKEN)
github = Github(GITHUB_TOKEN)
repo = github.get_repo(REPO_NAME)

# ============================
# توابع کمکی
# ============================

def load_playlist_from_github():
    """لیست آهنگ‌ها را از فایل JSON در گیت‌هاب بارگذاری می‌کند."""
    try:
        file_content = repo.get_contents(JSON_FILE_PATH).decoded_content.decode("utf-8")
        return json.loads(file_content)
    except Exception:
        return []

def save_playlist_to_github(playlist):
    """لیست آهنگ‌ها را در فایل JSON در گیت‌هاب ذخیره می‌کند."""
    try:
        file_content = repo.get_contents(JSON_FILE_PATH)
        repo.update_file(
            file_content.path,
            "Update playlist.json",
            json.dumps(playlist, ensure_ascii=False, indent=4),
            file_content.sha,
        )
    except Exception:
        repo.create_file(
            JSON_FILE_PATH,
            "Create playlist.json",
            json.dumps(playlist, ensure_ascii=False, indent=4),
        )

# ============================
# هندلرهای ربات
# ============================

@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    """ارسال پیام خوش‌آمدگویی به کاربر."""
    welcome_message = (
        "سلام! 👋\n"
        "برای افزودن یک آهنگ، به ترتیب پیام‌های زیر را بفرستید:\n"
        "1️⃣ نام آهنگ\n"
        "2️⃣ نام خواننده\n"
        "3️⃣ لینک آهنگ\n"
        "هر مرحله را جداگانه ارسال کنید."
    )
    bot.reply_to(message, welcome_message)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """دریافت و پردازش پیام‌های کاربر."""
    chat_id = message.chat.id
    user_step = bot.get_chat_data(chat_id).get("step", 0)
    user_data = bot.get_chat_data(chat_id).get("data", {})

    if user_step == 0:
        bot.reply_to(message, "لطفاً نام آهنگ را وارد کنید:")
        bot.set_chat_data(chat_id, {"step": 1, "data": {}})
    elif user_step == 1:
        user_data["name"] = message.text.strip()
        bot.reply_to(message, "نام خواننده را وارد کنید:")
        bot.set_chat_data(chat_id, {"step": 2, "data": user_data})
    elif user_step == 2:
        user_data["artist"] = message.text.strip()
        bot.reply_to(message, "لینک آهنگ را وارد کنید:")
        bot.set_chat_data(chat_id, {"step": 3, "data": user_data})
    elif user_step == 3:
        user_data["url"] = message.text.strip()
        playlist = load_playlist_from_github()
        playlist.append(user_data)
        save_playlist_to_github(playlist)
        bot.reply_to(message, "آهنگ با موفقیت ذخیره شد! ✅")
        bot.set_chat_data(chat_id, {"step": 0, "data": {}})
    else:
        bot.reply_to(message, "لطفاً دوباره تلاش کنید.")
        bot.set_chat_data(chat_id, {"step": 0, "data": {}})

# ============================
# اجرای ربات
# ============================

if __name__ == "__main__":
    bot.infinity_polling()
