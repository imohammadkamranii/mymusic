import os
import json
import requests
import base64
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio
import logging

# تنظیم لاگینگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class MusicBotManager:
    def __init__(self):
        self.bot_token = os.getenv('7693573912:AAH5GlCeMvYolHuq8BckIEKgbDogcg6sldM')
        self.github_token = os.getenv('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')
        self.github_username = os.getenv('imohammadkamranii')  # مثل imohammadkamrani
        self.github_repo = os.getenv('imohammadkamranii.github.io')  # مثل imohammadkamrani.github.io
        self.playlist_file = 'playlist.json'
        
        # بررسی متغیرهای محیطی
        if not self.bot_token:
            logger.error("TELEGRAM_BOT_TOKEN تنظیم نشده است!")
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        
        if not self.github_token:
            logger.error("GITHUB_TOKEN تنظیم نشده است!")
            raise ValueError("GITHUB_TOKEN is required")
            
        if not self.github_username:
            logger.error("GITHUB_USERNAME تنظیم نشده است!")
            raise ValueError("GITHUB_USERNAME is required")
            
        if not self.github_repo:
            logger.error("GITHUB_REPO تنظیم نشده است!")
            raise ValueError("GITHUB_REPO is required")
            
        logger.info(f"Bot Token Length: {len(self.bot_token)}")
        logger.info(f"GitHub Username: {self.github_username}")
        logger.info(f"GitHub Repo: {self.github_repo}")
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پیام خوش‌آمدگویی"""
        welcome_message = """
🎵 سلام! به ربات موزیک خوش اومدی!

برای اضافه کردن موزیک به پلی‌لیست:
🎤 فایل صوتی (Voice) ارسال کن
🎵 فایل MP3 ارسال کن
📱 فایل Audio ارسال کن

موزیک‌هات روی سایتت نمایش داده میشن! 🎶
        """
        await update.message.reply_text(welcome_message)

    async def handle_audio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش فایل‌های صوتی"""
        try:
            # بررسی نوع فایل
            audio_file = None
            file_name = None
            
            if update.message.voice:
                audio_file = update.message.voice
                file_name = f"voice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ogg"
            elif update.message.audio:
                audio_file = update.message.audio
                file_name = audio_file.file_name or f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
            elif update.message.document and update.message.document.mime_type and 'audio' in update.message.document.mime_type:
                audio_file = update.message.document
                file_name = audio_file.file_name
            
            if not audio_file:
                await update.message.reply_text("❌ لطفاً فقط فایل صوتی ارسال کنید!")
                return
                
            await update.message.reply_text("⏳ در حال پردازش فایل...")
            
            # دریافت فایل از تلگرام
            file = await context.bot.get_file(audio_file.file_id)
            file_url = file.file_path
            
            # دانلود فایل
            response = requests.get(file_url)
            if response.status_code != 200:
                await update.message.reply_text("❌ خطا در دانلود فایل!")
                return
                
            # آپلود به GitHub
            success = await self.upload_to_github(response.content, file_name)
            
            if success:
                # به‌روزرسانی playlist.json
                await self.update_playlist(file_name, update.message.from_user.first_name)
                await update.message.reply_text(f"✅ فایل {file_name} با موفقیت اضافه شد!")
            else:
                await update.message.reply_text("❌ خطا در آپلود فایل به GitHub!")
                
        except Exception as e:
            logger.error(f"خطا در پردازش فایل صوتی: {e}")
            await update.message.reply_text("❌ خطا در پردازش فایل!")

    async def upload_to_github(self, file_content, file_name):
        """آپلود فایل به GitHub"""
        try:
            url = f"https://api.github.com/repos/{self.github_username}/{self.github_repo}/contents/music/{file_name}"
            
            # کدگذاری فایل به base64
            encoded_content = base64.b64encode(file_content).decode('utf-8')
            
            data = {
                "message": f"Add music file: {file_name}",
                "content": encoded_content
            }
            
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            response = requests.put(url, json=data, headers=headers)
            return response.status_code == 201
            
        except Exception as e:
            logger.error(f"خطا در آپلود به GitHub: {e}")
            return False

    async def get_current_playlist(self):
        """دریافت پلی‌لیست فعلی از GitHub"""
        try:
            url = f"https://api.github.com/repos/{self.github_username}/{self.github_repo}/contents/{self.playlist_file}"
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                content = response.json()
                playlist_data = json.loads(base64.b64decode(content['content']).decode('utf-8'))
                return playlist_data, content['sha']
            else:
                # اگر فایل وجود نداشت، یک پلی‌لیست خالی برگردان
                return {"songs": []}, None
                
        except Exception as e:
            logger.error(f"خطا در دریافت پلی‌لیست: {e}")
            return {"songs": []}, None

    async def update_playlist(self, file_name, uploader_name):
        """به‌روزرسانی پلی‌لیست"""
        try:
            # دریافت پلی‌لیست فعلی
            playlist_data, sha = await self.get_current_playlist()
            
            # اضافه کردن آهنگ جدید
            new_song = {
                "title": file_name.rsplit('.', 1)[0],  # نام بدون پسوند
                "url": f"https://{self.github_username}.github.io/music/{file_name}",
                "uploader": uploader_name,
                "upload_date": datetime.now().isoformat()
            }
            
            playlist_data["songs"].append(new_song)
            
            # آپلود پلی‌لیست به‌روزشده
            url = f"https://api.github.com/repos/{self.github_username}/{self.github_repo}/contents/{self.playlist_file}"
            
            encoded_content = base64.b64encode(json.dumps(playlist_data, indent=2, ensure_ascii=False).encode('utf-8')).decode('utf-8')
            
            data = {
                "message": f"Update playlist: Add {file_name}",
                "content": encoded_content
            }
            
            if sha:
                data["sha"] = sha
            
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            response = requests.put(url, json=data, headers=headers)
            return response.status_code in [200, 201]
            
        except Exception as e:
            logger.error(f"خطا در به‌روزرسانی پلی‌لیست: {e}")
            return False

    async def list_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش لیست آهنگ‌ها"""
        try:
            playlist_data, _ = await self.get_current_playlist()
            songs = playlist_data.get("songs", [])
            
            if not songs:
                await update.message.reply_text("🎵 هنوز آهنگی اضافه نشده!")
                return
            
            message = "🎵 لیست آهنگ‌ها:\n\n"
            for i, song in enumerate(songs[-10:], 1):  # آخرین 10 آهنگ
                message += f"{i}. {song['title']}\n"
                message += f"   👤 {song['uploader']}\n\n"
            
            await update.message.reply_text(message)
            
        except Exception as e:
            logger.error(f"خطا در نمایش لیست: {e}")
            await update.message.reply_text("❌ خطا در دریافت لیست آهنگ‌ها!")

def main():
    """تابع اصلی"""
    bot_manager = MusicBotManager()
    
    # ساخت Application
    application = Application.builder().token(bot_manager.bot_token).build()
    
    # اضافه کردن هندلرها
    application.add_handler(CommandHandler("start", bot_manager.start_command))
    application.add_handler(CommandHandler("list", bot_manager.list_command))
    application.add_handler(MessageHandler(filters.VOICE | filters.AUDIO | 
                                        filters.Document.AUDIO, bot_manager.handle_audio))
    
    # شروع ربات
    print("🤖 ربات شروع شد...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
