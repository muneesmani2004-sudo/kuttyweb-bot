import os
import requests
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ══════════════════════════════════════
# CONFIG
# ══════════════════════════════════════
BOT_TOKEN = "8280311962:AAEjSIObBnkGMjogBvDVjwScqaMtIqM1EbM"
DOOD_API_KEY = "559711b5fn9i7yrsq2o9fb"
DOOD_API = "https://doodapi.co/api"

# Your Telegram user ID (bot only responds to you!)
# Get your ID by messaging @userinfobot on Telegram
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ══════════════════════════════════════
# DOODSTREAM FUNCTIONS
# ══════════════════════════════════════

def dood_get_server():
    """Get upload server from Doodstream"""
    try:
        r = requests.get(f"{DOOD_API}/upload/server?key={DOOD_API_KEY}", timeout=10)
        data = r.json()
        if data.get("status") == 200:
            return data["result"]
        return None
    except Exception as e:
        logger.error(f"Get server error: {e}")
        return None

def dood_upload_file(file_path, filename):
    """Upload file to Doodstream"""
    server = dood_get_server()
    if not server:
        return None
    try:
        with open(file_path, "rb") as f:
            r = requests.post(
                server,
                data={"api_key": DOOD_API_KEY},
                files={"file": (filename, f)},
                timeout=300
            )
        data = r.json()
        logger.info(f"Upload response: {data}")
        if data.get("status") == 200:
            files = data.get("files", [])
            if files:
                return files[0]
        return None
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return None

def dood_remote_upload(url, filename):
    """Remote upload URL to Doodstream"""
    try:
        r = requests.get(
            f"{DOOD_API}/remote/add",
            params={
                "key": DOOD_API_KEY,
                "url": url,
                "filename": filename
            },
            timeout=30
        )
        data = r.json()
        logger.info(f"Remote upload response: {data}")
        if data.get("status") == 200:
            return data.get("result")
        return None
    except Exception as e:
        logger.error(f"Remote upload error: {e}")
        return None

def dood_check_status(file_code):
    """Check remote upload status"""
    try:
        r = requests.get(
            f"{DOOD_API}/remote/list",
            params={"key": DOOD_API_KEY},
            timeout=10
        )
        data = r.json()
        if data.get("status") == 200:
            for item in data.get("result", []):
                if item.get("file_code") == file_code:
                    return item
        return None
    except:
        return None

# ══════════════════════════════════════
# BOT HANDLERS
# ══════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if ADMIN_ID != 0 and user_id != ADMIN_ID:
        await update.message.reply_text("⛔ Unauthorized!")
        return
    
    await update.message.reply_text(
        "🎬 *KuttyWeb Movie Uploader Bot*\n\n"
        "Send me any movie/video file and I'll upload it to Doodstream automatically!\n\n"
        "📤 *How to use:*\n"
        "1. Send a video file\n"
        "2. Bot uploads to Doodstream\n"
        "3. Get stream + download links\n"
        "4. Paste links in Admin Panel ✅\n\n"
        "🔗 *Commands:*\n"
        "/start - Show this message\n"
        "/account - Check Doodstream account\n"
        "/help - Help",
        parse_mode="Markdown"
    )

async def account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if ADMIN_ID != 0 and user_id != ADMIN_ID:
        await update.message.reply_text("⛔ Unauthorized!")
        return
    
    try:
        r = requests.get(f"{DOOD_API}/account/info?key={DOOD_API_KEY}", timeout=10)
        data = r.json()
        if data.get("status") == 200:
            result = data["result"]
            storage_used = int(result.get("storage_used", 0))
            storage_left = int(result.get("storage_left", 0))
            used_gb = storage_used / (1024**3)
            left_gb = storage_left / (1024**3)
            await update.message.reply_text(
                f"📊 *Doodstream Account*\n\n"
                f"📧 Email: {result.get('email','N/A')}\n"
                f"💰 Balance: ${result.get('balance','0')}\n"
                f"📦 Storage Used: {used_gb:.2f} GB\n"
                f"💾 Storage Left: {left_gb:.2f} GB\n"
                f"⭐ Premium: {result.get('premim_expire','N/A')}",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("❌ Could not fetch account info!")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if ADMIN_ID != 0 and user_id != ADMIN_ID:
        await update.message.reply_text("⛔ Unauthorized!")
        return

    # Get file info
    video = update.message.video or update.message.document
    if not video:
        await update.message.reply_text("❌ Please send a video file!")
        return

    filename = getattr(video, "file_name", None) or f"movie_{video.file_id[:8]}.mp4"
    file_size_mb = video.file_size / (1024 * 1024) if video.file_size else 0

    msg = await update.message.reply_text(
        f"📥 *Received:* `{filename}`\n"
        f"📦 *Size:* {file_size_mb:.1f} MB\n\n"
        f"⏳ Downloading from Telegram...",
        parse_mode="Markdown"
    )

    try:
        # Download file from Telegram
        file = await video.get_file()
        file_path = f"/tmp/{filename}"
        
        await msg.edit_text(
            f"📥 *File:* `{filename}`\n"
            f"📦 *Size:* {file_size_mb:.1f} MB\n\n"
            f"⬇️ Downloading... (may take a few minutes)",
            parse_mode="Markdown"
        )
        
        await file.download_to_drive(file_path)

        await msg.edit_text(
            f"📥 *File:* `{filename}`\n"
            f"📦 *Size:* {file_size_mb:.1f} MB\n\n"
            f"📤 Uploading to Doodstream...",
            parse_mode="Markdown"
        )

        # Upload to Doodstream
        result = dood_upload_file(file_path, filename)

        # Clean up temp file
        if os.path.exists(file_path):
            os.remove(file_path)

        if result:
            file_code = result.get("filecode", "")
            stream_url = f"https://dood.watch/e/{file_code}"
            download_url = f"https://dood.watch/d/{file_code}"
            embed_url = f"https://dood.watch/e/{file_code}"

            await msg.edit_text(
                f"✅ *Upload Successful!*\n\n"
                f"🎬 *File:* `{filename}`\n"
                f"📦 *Size:* {file_size_mb:.1f} MB\n\n"
                f"🔗 *Stream Link:*\n`{stream_url}`\n\n"
                f"⬇️ *Download Link:*\n`{download_url}`\n\n"
                f"📋 *Embed Code:*\n`{embed_url}`\n\n"
                f"👆 Copy links → Paste in Admin Panel!",
                parse_mode="Markdown"
            )
        else:
            await msg.edit_text(
                f"❌ *Upload Failed!*\n\n"
                f"Could not upload `{filename}` to Doodstream.\n"
                f"Please try again or check your API key.",
                parse_mode="Markdown"
            )

    except Exception as e:
        logger.error(f"Error handling video: {e}")
        if os.path.exists(f"/tmp/{filename}"):
            os.remove(f"/tmp/{filename}")
        await msg.edit_text(
            f"❌ *Error:* {str(e)}\n\nPlease try again!",
            parse_mode="Markdown"
        )

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle direct URL uploads"""
    user_id = update.effective_user.id
    if ADMIN_ID != 0 and user_id != ADMIN_ID:
        return

    text = update.message.text.strip()
    if not text.startswith("http"):
        return

    msg = await update.message.reply_text(
        f"🔗 *URL received!*\n\n⏳ Starting remote upload to Doodstream...",
        parse_mode="Markdown"
    )

    filename = text.split("/")[-1] or "movie.mp4"
    result = dood_remote_upload(text, filename)

    if result:
        file_code = result.get("filecode", "")
        await msg.edit_text(
            f"✅ *Remote Upload Started!*\n\n"
            f"📋 File Code: `{file_code}`\n\n"
            f"⏳ Processing... (takes a few minutes)\n\n"
            f"🔗 Stream: `https://dood.watch/e/{file_code}`\n"
            f"⬇️ Download: `https://dood.watch/d/{file_code}`",
            parse_mode="Markdown"
        )
    else:
        await msg.edit_text("❌ Remote upload failed! Try sending the file directly.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *KuttyWeb Bot Help*\n\n"
        "📤 *Send video file* → Auto uploads to Doodstream\n"
        "🔗 *Send URL* → Remote upload to Doodstream\n"
        "/account → Check storage & balance\n\n"
        "✅ *After upload:*\n"
        "Copy the stream link\n"
        "→ Go to kuttyweb.online/admin.html\n"
        "→ Add Movie → Download Links\n"
        "→ Paste link → Save ✅",
        parse_mode="Markdown"
    )

# ══════════════════════════════════════
# MAIN
# ══════════════════════════════════════
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("account", account))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_video))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    
    print("🤖 KuttyWeb Bot is running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
