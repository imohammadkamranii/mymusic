import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import aiohttp
import asyncio

# تنظیم لاگینگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(name)  # اصلاح به name

class MusicBotManager:
    def init(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.webhook_url = 'https://mymusic-u0ry.onrender.com/webhook'  # آدرس Webhook
        
        # دیباگ
        print(f"TELEGRAM_BOT_TOKEN: {self.bot_token}")
        print(f"WEBHOOK_URL: {self.webhook_url}")
        logger.info(f"TELEGRAM_BOT_TOKEN: {'Set' if self.bot_token else 'Not Set'}")
        logger.info(f"WEBHOOK_URL: {self.webhook_url}")
        
        if not self.bot_token:
            logger.error("TELEGRAM_BOT_TOKEN is required!")
            raise ValueError("TELEGRAM_BOT_TOKEN is required")

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پیام خوش‌آمدگویی"""
        await update.message.reply_text(
            "🎵 سلام! به ربات موزیک خوش اومدی!\n"
            "فعلاً فقط می‌تونی دستورات رو تست کنی.\n"
            "دستور /list برای نمایش لیست آهنگ‌ها (فعلاً غیرفعاله)."
        )

    async def list_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش لیست آهنگ‌ها (موقتاً غیرفعال)"""
        await update.message.reply_text("⚠️ لیست آهنگ‌ها فعلاً غیرفعاله.")

async def main():
    """تابع اصلی"""
    bot_manager = MusicBotManager()
    application = Application.builder().token(bot_manager.bot_token).build()
    
    application.add_handler(CommandHandler("start", bot_manager.start_command))
    application.add_handler(CommandHandler("list", bot_manager.list_command))
    
    # تنظیم Webhook
    await application.bot.set_webhook(bot_manager.webhook_url)
    print(f"🤖 Webhook تنظیم شد: {bot_manager.webhook_url}")
    
    # راه‌اندازی سرور برای Webhook
    app = aiohttp.web.Application()
    async def webhook_handler(request):
        update = Update.de_json(await request.json(), application.bot)
        await application.process_update(update)
        return aiohttp.web.Response()
    
    app.router.add_post('/webhook', webhook_handler)
    
    async with aiohttp.web.AppRunner(app) as runner:
        await runner.setup()
        site = aiohttp.web.TCPSite(runner, '0.0.0.0', int(os.getenv('PORT', 8080)))
        await site.start()
        print(f"🤖 سرور روی پورت {os.getenv('PORT', 8080)} اجرا شد...")
        await asyncio.Event().wait()  # نگه داشتن سرور

if name == 'main':
    asyncio.run(main())
