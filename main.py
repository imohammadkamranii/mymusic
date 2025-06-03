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
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.github_token = os.getenv('GITHUB_TOKEN', '')  # اختیاری
        self.github_username = os.getenv('GITHUB_USERNAME', 'imohammadkamranii')  # پیش‌فرض
        self.github_repo = os.getenv('GITHUB_REPO', 'mymusic')  # پیش‌فرض
        self.base_path = 'mymusic'
        self.playlist_file = f'{self.base_path}/playlist.json'
        self.music_dir = f'{self.base_path}/music'
        
        # دیباگ
        print(f"TELEGRAM_BOT_TOKEN: {self.bot_token}")
        logger.info(f"TELEGRAM_BOT_TOKEN: {'Set' if self.bot_token else 'Not Set'}")
        
        # فقط چک کردن TELEGRAM_BOT_TOKEN
        if not self.bot_token:
            logger.error("TELEGRAM_BOT_TOKEN تنظیم نشده است!")
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        
        logger.info(f"Bot initialized with GitHub repo: {self.github_username}/{self.github_repo}")

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پیام خوش‌آمدگویی"""
        await update.message.reply_text(
            "🎵 سلام! به ربات موزیک خوش اومدی!\n\n"
            "برای اضافه کردن موزیک:\n"
            "🎤 فایل صوتی (Voice) ارسال کن\n"
            "🎵 فایل MP3 یا Audio ارسال کن\n\n"
            "موزیک‌ها روی سایت نمایش داده می‌شن! 🎶"
        )

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
                await update.message.reply_text("❌ فقط فایل صوتی بفرست!")
                return
                
            if audio_file.file_size > 20 * 1024 * 1024:
                await update.message.reply_text("❌ فایل باید زیر 20 مگابایت باشه!")
                return
                
            await update.message.reply_text("⏳ در حال پردازش...")
            
            file = await context.bot.get_file(audio_file.file_id)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(file.file_path) as response:
                    if response.status != 200:
                        await update.message.reply_text("❌ خطا در دانلود فایل!")
                        return
                    file_content = await response.read()
            
            if self.github_token and self.github_username and self.github_repo:
                await self.ensure_music_directory()
                success = await self.upload_to_github(file_content, file_name)
                if success:
                    await self.ensure_playlist_file()
                    await self.update_playlist(file_name, update.message.from_user.first_name)
                    await update.message.reply_text(f"✅ فایل {file_name} اضافه شد!")
                else:
                    await update.message.reply_text("❌ خطا در آپلود به GitHub!")
            else:
                await update.message.reply_text("⚠️ آپلود به GitHub غیرفعاله (متغیرهای GitHub تنظیم نشدن).")
                
        except Exception as e:
            logger.error(f"خطا در پردازش فایل: {e}")
            await update.message.reply_text("❌ خطا در پردازش فایل!")

    async def ensure_music_directory(self):
        """ایجاد پوشه mymusic/music در GitHub"""
        try:
            url = f"https://api.github.com/repos/{self.github_username}/{self.github_repo}/contents/{self.music_dir}/.gitkeep"
            headers = {"Authorization": f"token {self.github_token}", "Accept": "application/vnd.github.v3+json"}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 404:
                        data = {"message": "Create music directory", "content": base64.b64encode(b"").decode('utf-8')}
                        async with session.put(url, json=data, headers=headers) as put_response:
                            if put_response.status not in [201, 200]:
                                logger.error(f"خطا در ایجاد پوشه: {await put_response.text()}")
        except Exception as e:
            logger.error(f"خطا در ایجاد پوشه: {e}")

    async def ensure_playlist_file(self):
        """ایجاد فایل playlist.json در GitHub"""
        try:
            url = f"https://api.github.com/repos/{self.github_username}/{self.github_repo}/contents/{self.playlist_file}"
            headers = {"Authorization": f"token {self.github_token}", "Accept": "application/vnd.github.v3+json"}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 404:
                        initial_content = {"songs": []}
                        encoded_content = base64.b64encode(json.dumps(initial_content, indent=2, ensure_ascii=False).encode('utf-8')).decode('utf-8')
                        data = {"message": "Create playlist.json", "content": encoded_content}
                        async with session.put(url, json=data, headers=headers) as put_response:
                            if put_response.status not in [201, 200]:
                                logger.error(f"خطا در ایجاد playlist.json: {await put_response.text()}")
        except Exception as e:
            logger.error(f"خطا در ایجاد playlist.json: {e}")

    async def upload_to_github(self, file_content, file_name):
        """آپلود فایل به GitHub"""
        try:
            url = f"https://api.github.com/repos/{self.github_username}/{self.github_repo}/contents/{self.music_dir}/{file_name}"
            encoded_content = base64.b64encode(file_content).decode('utf-8')
            data = {"message": f"Add {file_name}", "content": encoded_content}
            headers = {"Authorization": f"token {self.github_token}", "Accept": "application/vnd.github.v3+json"}
            
            async with aiohttp.ClientSession() as session:
                async with session.put(url, json=data, headers=headers) as response:
                    if response.status == 201:
                        return True
                    elif response.status == 422:
                        await self.handle_file_conflict(file_name)
                        return False
                    else:
                        logger.error(f"خطا در آپلود: {await response.text()}")
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
        
        logger.warning(f"فایل {file_name} تکراریه، نام جدید: {new_file_name}")

    async def file_exists_in_github(self, file_name):
        """بررسی وجود فایل در GitHub"""
        url = f"https://api.github.com/repos/{self.github_username}/{self.github_repo}/contents/{self.music_dir}/{file_name}"
        headers = {"Authorization": f"token {self.github_token}", "Accept": "application/vnd.github.v3+json"}
        async with aiohttp.ClientSession() as session:
            async with session.head(url, headers=headers) as response:
                return response.status == 200

    async def get_current_playlist(self):
        """دریافت پلی‌لیست از GitHub"""
        try:
            url = f"https://api.github.com/repos/{self.github_username}/{self.github_repo}/contents/{self.playlist_file}"
            headers = {"Authorization": f"token {self.github_token}", "Accept": "application/vnd.github.v3+json"}
            
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
            encoded_content = base64.b64encode(json.dumps(playlist_data, indent=2, ensure_ascii=False).encode('utf-8')).decode('utf-8')
            data = {"message": f"Add {file_name} to playlist", "content": encoded_content}
            if sha:
                data["sha"] = sha
            
            headers = {"Authorization": f"token {self.github_token}", "Accept": "application/vnd.github.v3+json"}
            
            async with aiohttp.ClientSession() as session:
                async with session.put(url, json=data, headers=headers) as response:
                    return response.status in [200, 201]
        except Exception as e:
            logger.error(f"خطا در به‌روزرسانی پلی‌لیست: {e}")
            return False

    async def list_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش لیست آهنگ‌ها"""
        try:
            if not self.github_token or not self.github_username or not self.github_repo:
                await update.message.reply_text("⚠️ لیست آهنگ‌ها غیرفعاله (متغیرهای GitHub تنظیم نشدن).")
                return
                
            playlist_data, _ = await self.get_current_playlist()
            songs = playlist_data.get("songs", [])
            
            if not songs:
                await update.message.reply_text("🎵 هنوز آهنگی اضافه نشده!")
                return
            
            message = "🎵 لیست آهنگ‌ها:\n\n"
            for i, song in enumerate(songs[-10:], 1):
                message += f"{i}. {song['title']}\n👤 {song['uploader']}\n\n"
            
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
    application.add_handler(MessageHandler(filters.VOICE | filters.AUDIO | filters.Document.AUDIO, bot_manager.handle_audio))
    
    print("🤖 ربات شروع شد...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
