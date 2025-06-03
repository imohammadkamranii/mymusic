# main.py

import json
import re
import os
from telebot import TeleBot

# ============================
# ۱) تنظیمات اولیه
# ============================
# برای امنیت، توصیه می‌شود توکن تلگرام را به صورت متغیر محیطی ذخیره کنید.
# در لوکال می‌توانید فایل .env بسازید و BOT_TOKEN=your_token را داخل آن قرار دهید،
# و سپس از python-dotenv برای بارگذاری استفاده کنید.
#
# اما در این مثال ساده، فرض می‌کنیم متغیر محیطی تعریف شده است:
BOT_TOKEN = ("7693573912:AAH5GlCeMvYolHuq8BckIEKgbDogcg6sldM")  # اگر در متغیر محیطی نباشد، توکن مستقیم می‌آید

# مسیر فایل JSON (در همان مسیری که main.py قرار دارد)
JSON_PATH = "playlist.json"

# ایجاد شیء ربات
bot = TeleBot(BOT_TOKEN, parse_mode=None)


# ============================
# ۲) تابع بارگذاری/ذخیره‌سازی JSON
# ============================
def load_playlist():
    """
    فایل playlist.json را باز می‌کند و به صورت لیست پایتون برمی‌گرداند.
    اگر فایل وجود نداشته باشد یا خطایی در خواندن باشد، یک لیست خالی بازمی‌گرداند.
    """
    try:
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_playlist(playlist: list):
    """
    لیست پل‌لیست را (که شامل دیکشنری‌های آهنگ است) در فایل JSON ذخیره می‌کند.
    """
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(playlist, f, indent=4, ensure_ascii=False)


# ============================
# ۳) هندلر ربات برای پیام‌های متنی
# ============================
@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    """
    وقتی کاربر دستور /start یا /help می‌فرستد، پیام راهنما نمایش داده می‌شود.
    """
    tip = (
        "سلام 😊\n\n"
        "برای افزودن آهنگ، پیام خود را در این فرمت بفرستید:\n"
        "<نام آهنگ> از <نام خواننده> <لینک آهنگ>\n\n"
        "مثال:\n"
        "ردپا از حصین https://example.com/song.mp3"
    )
    bot.reply_to(message, tip)


@bot.message_handler(func=lambda msg: True, content_types=["text"])
def handle_text_message(message):
    """
    این تابع برای هر پیام متنی فراخوانی می‌شود:
    1. متن را بررسی می‌کند که دقیقاً یک URL داشته باشد.
    2. بخش قبل از لینک را با ' از ' تفکیک می‌کند تا نام آهنگ و نام خواننده استخراج شود.
    3. در صورت موفقیت، آهنگ جدید را در playlist.json ذخیره می‌کند.
    4. در صورت خطا، پیام مناسبی به کاربر ارسال می‌کند.
    """
    text = message.text.strip()

    try:
        # ابتدا چک می‌کنیم که حداقل یک URL (http/https) وجود داشته باشد
        # و دقیقاً در انتهای متن یک URL قرار دارد.
        pattern = r"^(.+)\s+(https?://\S+)$"
        m = re.match(pattern, text)
        if not m:
            raise ValueError("فرمت پیام صحیح نیست. از الگوی زیر استفاده کنید:\n"
                             "نام آهنگ از نام خواننده لینک آهنگ")

        # بخش قبل از لینک
        name_artist_part = m.group(1).strip()
        # خود لینک
        url_part = m.group(2).strip()

        # از کلمه ' از ' برای جداسازی نام آهنگ و خواننده استفاده می‌کنیم
        if " از " not in name_artist_part:
            raise ValueError("فرمت پیام درست نیست. بین نام آهنگ و خواننده کلمه ' از ' باشد.")

        name_part, artist_part = name_artist_part.split(" از ", 1)
        name_part = name_part.strip()
        artist_part = artist_part.strip()

        # اگر هر کدام خالی باشد، خطا بده
        if not name_part or not artist_part:
            raise ValueError("نام آهنگ یا نام خواننده نمی‌تواند خالی باشد.")

        # بارگذاری playlist فعلی از JSON
        playlist = load_playlist()

        # ایجاد ساختار دیکشنری جدید برای آهنگ
        new_song = {
            "name": name_part,
            "artist": artist_part,
            "url": url_part
        }

        # اضافه کردن آهنگ جدید به لیست و ذخیره مجدد
        playlist.append(new_song)
        save_playlist(playlist)

        # پاسخ موفقیت
        bot.reply_to(message, f"آهنگ «{name_part}» از «{artist_part}» با موفقیت اضافه شد ✅")
    except Exception as e:
        # ارسال پیام خطا به کاربر
        bot.reply_to(message, f"❌ خطا: {e}")


# ============================
# ۴) اجرای ربات (Polling)
# ============================
if __name__ == "__main__":
    print("🔄 ربات در حال اجراست...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
