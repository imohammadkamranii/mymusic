import json
import re
from telebot import TeleBot

# ============================
# ۱) تنظیمات اولیه
# ============================
BOT_TOKEN = "7693573912:AAH5GlCeMvYolHuq8BckIEKgbDogcg6sldM"  # توکن مستقیم
JSON_PATH = "playlist.json"

# ایجاد شیء ربات
bot = TeleBot(BOT_TOKEN, parse_mode=None)


# ============================
# ۲) تابع بارگذاری/ذخیره‌سازی JSON
# ============================
def load_playlist():
    try:
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_playlist(playlist: list):
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(playlist, f, indent=4, ensure_ascii=False)


# ============================
# ۳) هندلر ربات برای پیام‌های متنی
# ============================
@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
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
    text = message.text.strip()
    try:
        pattern = r"^(.+)\s+(https?://\S+)$"
        m = re.match(pattern, text)
        if not m:
            raise ValueError("فرمت پیام صحیح نیست. از الگوی زیر استفاده کنید:\n"
                             "نام آهنگ از نام خواننده لینک آهنگ")

        name_artist_part = m.group(1).strip()
        url_part = m.group(2).strip()

        if " از " not in name_artist_part:
            raise ValueError("فرمت پیام درست نیست. بین نام آهنگ و خواننده کلمه ' از ' باشد.")

        name_part, artist_part = name_artist_part.split(" از ", 1)
        name_part = name_part.strip()
        artist_part = artist_part.strip()

        if not name_part or not artist_part:
            raise ValueError("نام آهنگ یا نام خواننده نمی‌تواند خالی باشد.")

        playlist = load_playlist()

        new_song = {
            "name": name_part,
            "artist": artist_part,
            "url": url_part
        }

        playlist.append(new_song)
        save_playlist(playlist)

        bot.reply_to(message, f"آهنگ «{name_part}» از «{artist_part}» با موفقیت اضافه شد ✅")
    except Exception as e:
        bot.reply_to(message, f"❌ خطا: {e}")


# ============================
# ۴) اجرای ربات (Polling)
# ============================
if __name__ == "__main__":
    print("🔄 ربات در حال اجراست...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
