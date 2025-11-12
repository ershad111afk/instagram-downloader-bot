import os
import tempfile
import subprocess
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

BOT_TOKEN = "8499926122:AAEPtX6EMisAIRC2IaRANyeflGdSmVXzv9I"

# ✅ تابع بررسی عضویت
async def is_member(user_id, context):
    channel_username = "@evead_ir"  # 👈 نام کانالت
    try:
        member = await context.bot.get_chat_member(chat_id=channel_username, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        print(f"Check member error: {e}")
        return False

# ✅ تابع شروع /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not await is_member(user_id, context):
        join_button = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 عضویت در کانال", url="https://t.me/evead_ir")],
            [InlineKeyboardButton("✅ بررسی عضویت", callback_data="check_member")]
        ])
        await update.message.reply_text(
            "🔒 برای استفاده از ربات باید عضو کانال زیر بشی 👇",
            reply_markup=join_button
        )
        return

    keyboard = [
        [InlineKeyboardButton("📥 دانلود از اینستاگرام", callback_data="download")],
        [InlineKeyboardButton("ℹ️ درباره ربات", callback_data="about")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "سلام 👋\nمن یه ربات دانلودر اینستاگرامم!\nکافیه لینک پست یا ریلز اینستاگرام رو بفرستی تا دانلودش کنم 🎬",
        reply_markup=reply_markup
    )

# ✅ بررسی مجدد عضویت با دکمه “بررسی عضویت”
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == "check_member":
        if await is_member(user_id, context):
            await query.edit_message_text("✅ عضویتت تأیید شد! حالا می‌تونی از ربات استفاده کنی 😎")
            await start(update, context)
        else:
            join_button = InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 عضویت در کانال", url="https://t.me/evead_ir")],
                [InlineKeyboardButton("✅ بررسی عضویت", callback_data="check_member")]
            ])
            await query.edit_message_text(
                "❌ هنوز عضو کانال نشدی!\nبرای استفاده از ربات باید اول عضو بشی 👇",
                reply_markup=join_button
            )
            return

    elif query.data == "about":
        await query.edit_message_text(
            "من ساختهٔ ارشاد اسماعیلی‌ام 😎\nکافیه لینک پست یا ریلز اینستاگرام رو بفرستی تا دانلودش کنم.\n\n"
            "📌 نکته: پست باید عمومی باشه (Private نباشه).",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="menu")]])
        )
    elif query.data == "download":
        await query.edit_message_text("لینک پست اینستاگرام رو بفرست 📎")
    elif query.data == "menu":
        await start(update, context)

# ✅ تابع تشخیص لینک
def is_instagram_url(text: str) -> bool:
    return "instagram.com" in text or "instagr.am" in text

# ✅ دانلود پست یا ریلز اینستاگرام
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not await is_member(user_id, context):
        join_button = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 عضویت در کانال", url="https://t.me/evead_ir")],
            [InlineKeyboardButton("✅ بررسی عضویت", callback_data="check_member")]
        ])
        await update.message.reply_text(
            "🔒 برای استفاده از ربات باید عضو کانال بشی 👇",
            reply_markup=join_button
        )
        return

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
            if file_path.lower().endswith((".mp4", ".mov", ".mkv")):
                await msg.edit_text("🎬 در حال ارسال ویدیو...")
                await update.message.reply_video(video=open(file_path, "rb"))
            else:
                await msg.edit_text("🖼 در حال ارسال تصویر...")
                await update.message.reply_photo(photo=open(file_path, "rb"))

            await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ خطا:\n{str(e)}")

# ✅ اجرای ربات
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
