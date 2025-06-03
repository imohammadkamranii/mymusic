import os
import json
from telebot import TeleBot
import time

# ============================
# تنظیمات اولیه
# ============================

# توکن ربات
BOT_TOKEN = "7693573912:AAH5GlCeMvYolHuq8BckIEKgbDogcg6sldM"

# ایجاد شیء ربات
bot = TeleBot(BOT_TOKEN, parse_mode=None)

# مسیر فایل JSON
JSON_FILE = "playlist.json"

# ذخیره وضعیت فعلی کاربران
user_states = {}

# ============================
# توابع کمکی
# ============================

def load_playlist():
    """
    فایل playlist.json را بارگذاری می‌کند.
    اگر فایل وجود نداشته باشد، یک لیست خالی برمی‌گرداند.
    """
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_playlist(playlist):
    """
    لیست آهنگ‌ها را در فایل JSON ذخیره می‌کند.
    """
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(playlist, f, indent=4, ensure_ascii=False)

def reset_user_state(user_id):
    """
    وضعیت کاربر را ریست می‌کند.
    """
    if user_id in user_states:
        del user_states[user_id]

# ============================
# هندلرهای ربات
# ============================

@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    """
    پیام خوش‌آمدگویی به کاربر.
    """
    welcome_message = (
        "سلام! 👋\n"
        "برای افزودن آهنگ جدید، دستور /add را وارد کنید.\n"
    )
    bot.reply_to(message, welcome_message)

@bot.message_handler(commands=["add"])
def add_song_start(message):
    """
    شروع فرایند افزودن آهنگ.
    """
    user_id = message.chat.id
    user_states[user_id] = {"step": 1, "data": {}}
    bot.reply_to(message, "لطفاً نام آهنگ را وارد کنید:")

@bot.message_handler(func=lambda message: message.chat.id in user_states)
def handle_user_input(message):
    """
    پردازش ورودی کاربر در هر مرحله.
    """
    user_id = message.chat.id
    state = user_states[user_id]

    if state["step"] == 1:
        # ذخیره نام آهنگ و درخواست نام خواننده
        state["data"]["name"] = message.text.strip()
        state["step"] = 2
        bot.reply_to(message, "لطفاً نام خواننده را وارد کنید:")
    elif state["step"] == 2:
        # ذخیره نام خواننده و درخواست لینک آهنگ
        state["data"]["artist"] = message.text.strip()
        state["step"] = 3
        bot.reply_to(message, "لطفاً لینک آهنگ را وارد کنید:")
    elif state["step"] == 3:
        # ذخیره لینک آهنگ و تکمیل فرایند
        state["data"]["url"] = message.text.strip()
        song_data = state["data"]
        
        # ذخیره اطلاعات در JSON
        playlist = load_playlist()
        playlist.append(song_data)
        save_playlist(playlist)
        
        # پاسخ موفقیت
        bot.reply_to(
            message,
            f"آهنگ «{song_data['name']}» از «{song_data['artist']}» با لینک:\n{song_data['url']}\nبا موفقیت ذخیره شد ✅"
        )
        # ریست وضعیت کاربر
        reset_user_state(user_id)

# ============================
# اجرای ربات
# ============================

if __name__ == "__main__":
    print("🔄 ربات در حال اجراست...")
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"⚠️ خطا رخ داد: {e}")
            time.sleep(5)
