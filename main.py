import os
import json
from telebot import TeleBot
import time

# ============================
# تنظیمات اولیه
# ============================

# توکن ربات
BOT_TOKEN = os.getenv("7693573912:AAH5GlCeMvYolHuq8BckIEKgbDogcg6sldM")  # متغیر محیطی برای توکن ربات

# ایجاد شیء ربات
bot = TeleBot(BOT_TOKEN, parse_mode=None)

# مسیر فایل JSON
JSON_FILE = "playlist.json"

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
        "برای افزودن یک آهنگ به این فرمت پیام بفرستید:\n"
        "`نام آهنگ از نام خواننده لینک آهنگ`\n"
        "مثال:\n"
        "ردپا از حصین https://example.com/song.mp3"
    )
    bot.reply_to(message, welcome_message, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """
    پیام کاربر را پردازش کرده و اطلاعات آهنگ را در JSON ذخیره می‌کند.
    """
    text = message.text.strip()
    try:
        # بررسی فرمت پیام
        if " از " not in text or not text.endswith("http"):
            raise ValueError("فرمت پیام صحیح نیست. لطفاً به مثال داده شده دقت کنید.")

        # جدا کردن نام آهنگ، خواننده و لینک
        parts = text.rsplit(" ", 1)  # جدا کردن لینک
        name_artist, url = parts[0], parts[1]
        name, artist = name_artist.split(" از ")

        # بررسی عدم خالی بودن فیلدها
        if not name or not artist or not url:
            raise ValueError("تمام بخش‌های پیام (نام، خواننده و لینک) باید پر باشند.")

        # بارگذاری لیست قبلی و اضافه کردن آیتم جدید
        playlist = load_playlist()
        playlist.append({"name": name.strip(), "artist": artist.strip(), "url": url.strip()})
        save_playlist(playlist)

        # پاسخ موفقیت
        bot.reply_to(message, f"آهنگ «{name}» از «{artist}» با موفقیت ذخیره شد ✅")

    except Exception as e:
        bot.reply_to(message, f"❌ خطا: {str(e)}")

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
