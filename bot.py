import os
import tempfile
import subprocess
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

BOT_TOKEN = "8499926122:AAEPtX6EMisAIRC2IaRANyeflGdSmVXzv9I"

# --- /start command ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📥 دانلود از اینستاگرام", callback_data="download")],
        [InlineKeyboardButton("ℹ️ درباره ربات", callback_data="about")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "سلام 👋\nمن یه ربات دانلودر اینستاگرامم!\nبا من می‌تونی عکس یا ویدیو از پست، ریلز یا استوری بگیری.",
        reply_markup=reply_markup
    )

# --- منوی دکمه‌ها ---
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "about":
        await query.edit_message_text(
            "من ساختهٔ ارشاد اسماعیلی‌ام 😎\nکافیه لینک پست یا ریلز اینستاگرام رو برام بفرستی تا دانلودش کنم.\n\n"
            "📌 نکته: پست باید عمومی باشه (Private نباشه).",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="menu")]])
        )
    elif query.data == "download":
        await query.edit_message_text("لینک پست اینستاگرام رو بفرست 📎")
    elif query.data == "menu":
        await start(query, context)

# --- تابع تشخیص لینک ---
def is_instagram_url(text: str) -> bool:
    return "instagram.com" in text or "instagr.am" in text

# --- تابع دانلود ---
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not is_instagram_url(text):
        await update.message.reply_text("❌ لینک معتبر نیست، لطفاً لینک اینستاگرام بفرست.")
        return

    msg = await update.message.reply_text("⏳ در حال بررسی و دانلود فایل...")

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_template = os.path.join(tmpdir, "%(title)s.%(ext)s")
            cmd = [
                "python", "-m", "yt_dlp",
                "-f", "best",
                "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "--no-warnings",
                "-o", out_template,
                text
            ]

            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if proc.returncode != 0:
                await msg.edit_text("⚠️ خطا در دانلود:\n" + proc.stderr[:400])
                return

            files = os.listdir(tmpdir)
            if not files:
                await msg.edit_text("❌ فایلی برای ارسال پیدا نشد.")
                return

            file_path = os.path.join(tmpdir, files[0])
            size = os.path.getsize(file_path)

            if size <= 50 * 1024 * 1024:
                if file_path.lower().endswith((".mp4", ".mov", ".mkv")):
                    await msg.edit_text("🎬 در حال ارسال ویدیو...")
                    await update.message.reply_video(video=open(file_path, "rb"))
                else:
                    await msg.edit_text("🖼 در حال ارسال تصویر...")
                    await update.message.reply_photo(photo=open(file_path, "rb"))
                await msg.delete()
            else:
                await msg.edit_text("⚠️ فایل خیلی بزرگه (بیش از 50MB). لطفاً لینک کوتاه‌تر بفرست.")
    except Exception as e:
        await msg.edit_text(f"❌ خطا:\n{str(e)}")

# --- Flask برای Render ---
web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    web_app.run(host="0.0.0.0", port=8000)

# --- main ---
def main():
    # اجرای Flask در یک thread جدا
    threading.Thread(target=run_flask).start()

    # راه‌اندازی ربات تلگرام
    bot_app = ApplicationBuilder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CallbackQueryHandler(menu_handler))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

    print("🤖 Bot is running...")
    bot_app.run_polling()

if __name__ == "__main__":
    main()
