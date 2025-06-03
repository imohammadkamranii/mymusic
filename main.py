import os
import json
import base64
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio
import logging
import aiohttp

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
        self.github_username = os.getenv('imohammadkamranii')
        self.github_repo = os.getenv('imohammadkamranii.github.io/mymusic')
        self.playlist_file = 'playlist.json'
        self.music_dir = 'music'
        
        # بررسی متغیرهای محیطی
        for var, name in [
            (self.bot_token, "TELEGRAM_BOT_TOKEN"),
            (self.github_token, "GITHUB_TOKEN"),
            (self.github_username, "GITHUB_USERNAME"),
            (self.github_repo, "GITHUB_REPO")
        ]:
            if not var:
                logger.error(f"{name} تنظیم نشده است!")
                raise ValueError(f"{name} is required")
        
        logger.info(f"Bot initialized with GitHub repo: {self.github_username}/{self.github_repo}")

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
                file_name = audio_file.file_name or f"doc_audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
            
            if not audio_file:
                await update.message.reply_text("❌ لطفاً فقط فایل صوتی ارسال کنید!")
                return
                
            if audio_file.file_size > 20 * 1024 * 1024:  # محدودیت 20 مگابایت
                await update.message.reply_text("❌ فایل خیلی بزرگ است! حداکثر 20 مگابایت مجاز است.")
                return
                
            await update.message.reply_text("⏳ در حال پردازش فایل...")
            
            # دریافت فایل از تلگرام
            file = await context.bot.get_file(audio_file.file_id)
            
            # دانلود فایل
            async with aiohttp.ClientSession() as session:
                async with session.get(file.file_path) as response:
                    if response.status != 200:
                        await update.message.reply_text("❌ خطا در دانلود فایل!")
                        return
                    file_content = await response.read()
            
            # بررسی وجود پوشه music
            await self.ensure_music_directory()
            
            # آپلود به GitHub
            success = await self.upload_to_github(file_content, file_name)
            
            if success:
                # به‌روزرسانی playlist.json
                await self.ensure_playlist_file()
                await self.update_playlist(file_name, update.message.from_user.first_name)
                await update.message.reply_text(f"✅ فایل {file_name} با موفقیت اضافه شد!")
            else:
                await update.message.reply_text("❌ خطا در آپلود فایل به GitHub!")
                
        except Exception as e:
            logger.error(f"خطا در پردازش فایل صوتی: {e}")
            await update.message.reply_text("❌ خطا در پردازش فایل!")

    async def ensure_music_directory(self):
        """بررسی و ایجاد پوشه music در صورت عدم وجود"""
        try:
            url = f"https://api.github.com/repos/{self.github_username}/{self.github_repo}/contents/{self.music_dir}/.gitkeep"
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 404:
                        # پوشه وجود ندارد، فایل .gitkeep را آپلود می‌کنیم
                        data = {
                            "message": "Create music directory with .gitkeep",
                            "content": base64.b64encode(b"").decode('utf-8')
                        }
                        async with session.put(url, json=data, headers=headers) as put_response:
                            if put_response.status not in [201, 200]:
                                logger.error(f"خطا در ایجاد پوشه music: {await put_response.text()}")
                    elif response.status != 200:
                        logger.error(f"خطا در بررسی پوشه music: {await response.text()}")
        except Exception as e:
            logger.error(f"خطا در بررسی/ایجاد پوشه music: {e}")

    async def ensure_playlist_file(self):
        """بررسی و ایجاد فایل playlist.json در صورت عدم وجود"""
        try:
            url = f"https://api.github.com/repos/{self.github_username}/{self.github_repo}/contents/{self.playlist_file}"
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 404:
                        # فایل وجود ندارد، فایل اولیه ایجاد می‌کنیم
                        initial_content = {"songs": []}
                        encoded_content = base64.b64encode(
                            json.dumps(initial_content, indent=2, ensure_ascii=False).encode('utf-8')
                        ).decode('utf-8')
                        data = {
                            "message": "Create initial playlist.json",
                            "content": encoded_content
                        }
                        async with session.put(url, json=data, headers=headers) as put_response:
                            if put_response.status not in [201, 200]:
                                logger.error(f"خطا در ایجاد فایل playlist.json: {await put_response.text()}")
                    elif response.status != 200:
                        logger.error(f"خطا در بررسی فایل playlist.json: {await put_response.text()}")
        except Exception as e:
            logger.error(f"خطا در بررسی/ایجاد فایل playlist.json: {e}")

    async def upload_to_github(self, file_content, file_name):
        """آپلود فایل به GitHub"""
        try:
            url = f"https://api.github.com/repos/{self.github_username}/{self.github_repo}/contents/{self.music_dir}/{file_name}"
            encoded_content = base64.b64encode(file_content).decode('utf-8')
            data = {
                "message": f"Add music file: {file_name}",
                "content": encoded_content
            }
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.put(url, json=data, headers=headers) as response:
                    if response.status == 201:
                        return True
                    elif response.status == 422:  # فایل از قبل وجود دارد
                        await self.handle_file_conflict(file_name)
                        return False
                    else:
                        logger.error(f"خطا در آپلود فایل به GitHub: {await response.text()}")
                        return False
        except Exception as e:
            logger.error(f"خطا در آپلود به GitHub: {e}")
            return False

    async def handle_file_conflict(self, file_name):
        """مدیریت فایل‌های تکراری"""
        base, ext = os.path.splitext(file_name)
        counter = 1
        new_file_name = f"{base}_{counter}{ext}"
        
        while await self.file_exists_in_github(new_file_name):
            counter += 1
            new_file_name = f"{base}_{counter}{ext}"
        
        # دوباره تلاش برای آپلود
        # (می‌توانید منطق آپلود را اینجا تکرار کنید یا به کاربر اطلاع دهید)
        logger.warning(f"فایل {file_name} تکراری است، نام جدید: {new_file_name}")

    async def file_exists_in_github(self, file_name):
        """بررسی وجود فایل در GitHub"""
        url = f"https://api.github.com/repos/{self.github_username}/{self.github_repo}/contents/{self.music_dir}/{file_name}"
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        async with aiohttp.ClientSession() as session:
            async with session.head(url, headers=headers) as response:
                return response.status == 200

    async def get_current_playlist(self):
        """دریافت پلی‌لیست فعلی از GitHub"""
        try:
            url = f"https://api.github.com/repos/{self.github_username}/{self.github_repo}/contents/{self.playlist_file}"
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        content = await response.json()
                        playlist_data = json.loads(base64.b64decode(content['content']).decode('utf-8'))
                        return playlist_data, content['sha']
                    elif response.status == 404:
                        await self.ensure_playlist_file()
                        return {"songs": []}, None
                    else:
                        logger.error(f"خطا در دریافت پلی‌لیست: {await response.text()}")
                        return {"songs": []}, None
        except Exception as e:
            logger.error(f"خطا در دریافت پلی‌لیست: {e}")
            return {"songs": []}, None

    async def update_playlist(self, file_name, uploader_name):
        """به‌روزرسانی پلی‌لیست"""
        try:
            playlist_data, sha = await self.get_current_playlist()
            
            new_song = {
                "title": file_name.rsplit('.', 1)[0],
                "url": f"https://{self.github_username}.github.io/{self.music_dir}/{file_name}",
                "uploader": uploader_name,
                "upload_date": datetime.now().isoformat()
            }
            
            playlist_data["songs"].append(new_song)
            
            url = f"https://api.github.com/repos/{self.github_username}/{self.github_repo}/contents/{self.playlist_file}"
            encoded_content = base64.b64encode(
                json.dumps(playlist_data, indent=2, ensure_ascii=False).encode('utf-8')
            ).decode('utf-8')
            
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
            
            async with aiohttp.ClientSession() as session:
                async with session.put(url, json=data, headers=headers) as response:
                    return response.status in [200, 201]
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
            for i, song in enumerate(songs[-10:], 1):
                message += f"{i}. {song['title']}\n"
                message += f"   👤 {song['uploader']}\n\n"
            
            await update.message.reply_text(message)
        except Exception as e:
            logger.error(f"خطا در نمایش لیست: {e}")
            await update.message.reply_text("❌ خطا در دریافت لیست آهنگ‌ها!")

def main():
    """تابع اصلی"""
    bot_manager = MusicBotManager()
    application = Application.builder().token(bot_manager.bot_token).build()
    
    application.add_handler(CommandHandler("start", bot_manager.start_command))
    application.add_handler(CommandHandler("list", bot_manager.list_command))
    application.add_handler(MessageHandler(filters.VOICE | filters.AUDIO | 
                                        filters.Document.AUDIO, bot_manager.handle_audio))
    
    print("🤖 ربات شروع شد...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
