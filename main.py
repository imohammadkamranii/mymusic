import telebot
import requests
import base64
import json
import os
from decouple import config

# اطلاعات مورد نیاز از متغیرهای محیطی
BOT_TOKEN = config("7693573912:AAH5GlCeMvYolHuq8BckIEKgbDogcg6sldM")
GITHUB_TOKEN = config("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")
REPO_OWNER = config("imohammadkamranii")
REPO_NAME = config("mymusic")
FILE_PATH = "playlist.json"

# ربات تلگرام
bot = telebot.TeleBot(BOT_TOKEN)

# تابع آپدیت فایل JSON
def update_github_file(file_url):
    try:
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}

        # دریافت فایل JSON فعلی
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            response_json = response.json()
            old_content = json.loads(base64.b64decode(response_json['content']).decode())
            sha = response_json['sha']
        else:
            old_content = []
            sha = None

        # اضافه کردن لینک جدید
        old_content.append(file_url)
        new_content = json.dumps(old_content, indent=4)

        # به‌روزرسانی فایل در GitHub
        update_data = {
            "message": "Update playlist.json",
            "content": base64.b64encode(new_content.encode()).decode(),
            "sha": sha  # SHA ممکن است None باشد برای فایل‌های جدید
        }
        update_response = requests.put(url, headers=headers, data=json.dumps(update_data))
        return update_response.status_code == 200

    except Exception as e:
        print(f"خطایی رخ داد: {e}")
        return False

# مدیریت پیام‌های صوتی
@bot.message_handler(content_types=["audio", "voice"])
def handle_audio(message):
    try:
        file_id = message.audio.file_id if message.audio else message.voice.file_id
        file_info = bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"

        if update_github_file(file_url):
            bot.reply_to(message, "لینک فایل با موفقیت به لیست اضافه شد!")
        else:
            bot.reply_to(message, "خطایی رخ داد. لطفاً دوباره تلاش کنید.")
    except Exception as e:
        bot.reply_to(message, f"خطا: {e}")

# اجرای ربات
bot.polling()
