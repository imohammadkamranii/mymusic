import telebot
import json
import re

# تنظیمات
BOT_TOKEN = "7693573912:AAH5GlCeMvYolHuq8BckIEKgbDogcg6sldM"
bot = telebot.TeleBot(BOT_TOKEN)

FILE_PATH = "playlist.json"  # مسیر فایل JSON

# ذخیره آهنگ در فایل JSON
def save_song(song_data):
    try:
        with open(FILE_PATH, "r") as file:
            playlist = json.load(file)
    except FileNotFoundError:
        playlist = []

    playlist.append(song_data)

    with open(FILE_PATH, "w") as file:
        json.dump(playlist, file, indent=4)

# مدیریت پیام‌های متنی
@bot.message_handler(content_types=["text"])
def handle_text(message):
    text = message.text.strip()

    # استفاده از Regex برای استخراج نام آهنگ و لینک
    match = re.match(r"(.+)\s+(https?://\S+)", text)
    if match:
        name_artist = match.group(1)  # متن قبل از لینک
        link = match.group(2)         # لینک

        # جداسازی نام آهنگ و خواننده
        if " از " in name_artist:
            name, artist = name_artist.split(" از ", 1)
        else:
            name, artist = name_artist, "ناشناخته"

        # ذخیره اطلاعات در فایل
        song_data = {"name": name.strip(), "artist": artist.strip(), "link": link.strip()}
        save_song(song_data)

        bot.reply_to(message, f"آهنگ '{song_data['name']}' از '{song_data['artist']}' با موفقیت اضافه شد!")
    else:
        bot.reply_to(message, "فرمت پیام صحیح نیست! لطفاً به صورت زیر ارسال کنید:\nنام آهنگ از خواننده لینک آهنگ")

# اجرای ربات
bot.polling()
