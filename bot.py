import os
import requests
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ══════════════════════════════════
# CONFIG — already set for you!
# ══════════════════════════════════
BOT_TOKEN   = "8280311962:AAEjSIObBnkGMjogBvDVjwScqaMtIqM1EbM"
DOOD_KEY    = "559711b5fn9i7yrsq2o9fb"
DOOD_API    = "https://doodapi.co/api"
ADMIN_ID    = int(os.environ.get("ADMIN_ID", "0"))

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.INFO
)

# ══════════════════════════════════
# DOODSTREAM HELPERS
# ══════════════════════════════════
def get_upload_server():
    try:
        r = requests.get(f"{DOOD_API}/upload/server?key={DOOD_KEY}", timeout=15)
        d = r.json()
        if d.get("status") == 200:
            return d["result"]
    except Exception as e:
        logging.error(f"Server error: {e}")
    return None

def upload_to_dood(path, name):
    server = get_upload_server()
    if not server:
        return None
    try:
        with open(path, "rb") as f:
            r = requests.post(
                server,
                data={"api_key": DOOD_KEY},
                files={"file": (name, f)},
                timeout=600
            )
        d = r.json()
        logging.info(f"Upload result: {d}")
        if d.get("status") == 200:
            files = d.get("files", [])
            if files:
                return files[0].get("filecode")
    except Exception as e:
        logging.error(f"Upload error: {e}")
    return None

# ══════════════════════════════════
# BOT COMMANDS
# ══════════════════════════════════
def is_admin(uid):
    return ADMIN_ID == 0 or uid == ADMIN_ID

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Access denied!")
        return
    await update.message.reply_text(
        "🎬 KuttyWeb Uploader Bot\n\n"
        "Send any movie/video file\n"
        "I will upload it to Doodstream!\n\n"
        "Commands:\n"
        "/start - This message\n"
        "/account - Doodstream account info\n"
    )

async def cmd_account(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    try:
        r = requests.get(f"{DOOD_API}/account/info?key={DOOD_KEY}", timeout=10)
        d = r.json()
        if d.get("status") == 200:
            res = d["result"]
            used = int(res.get("storage_used", 0)) / (1024**3)
            left = int(res.get("storage_left", 0)) / (1024**3)
            await update.message.reply_text(
                f"📊 Doodstream Account\n\n"
                f"Email: {res.get('email')}\n"
                f"Balance: ${res.get('balance','0')}\n"
                f"Used: {used:.2f} GB\n"
                f"Left: {left:.2f} GB"
            )
        else:
            await update.message.reply_text("❌ Could not get account info")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def handle_file(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Access denied!")
        return

    video = (
        update.message.video or
        update.message.document
    )
    if not video:
        await update.message.reply_text("❌ Send a video file!")
        return

    name = getattr(video, "file_name", None) or f"movie_{video.file_unique_id}.mp4"
    size_mb = round((video.file_size or 0) / (1024*1024), 1)

    msg = await update.message.reply_text(
        f"📥 Received: {name}\n"
        f"Size: {size_mb} MB\n\n"
        f"⏳ Downloading from Telegram..."
    )

    path = f"/tmp/{name}"
    try:
        tg_file = await video.get_file()
        await tg_file.download_to_drive(path)

        await msg.edit_text(
            f"📥 {name} ({size_mb} MB)\n\n"
            f"📤 Uploading to Doodstream...\n"
            f"Please wait, this may take a few minutes..."
        )

        code = upload_to_dood(path, name)

        if code:
            await msg.edit_text(
                f"✅ Upload Successful!\n\n"
                f"🎬 File: {name}\n"
                f"📦 Size: {size_mb} MB\n\n"
                f"▶️ Stream Link:\n"
                f"https://dood.watch/e/{code}\n\n"
                f"⬇️ Download Link:\n"
                f"https://dood.watch/d/{code}\n\n"
                f"Copy link → Admin Panel → Add Movie ✅"
            )
        else:
            await msg.edit_text(
                f"❌ Upload failed for {name}\n"
                f"Please try again!"
            )
    except Exception as e:
        logging.error(f"Error: {e}")
        await msg.edit_text(f"❌ Error: {str(e)}")
    finally:
        if os.path.exists(path):
            os.remove(path)

# ══════════════════════════════════
# RUN
# ══════════════════════════════════
def main():
    print("🤖 KuttyWeb Bot starting...")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("account", cmd_account))
    app.add_handler(MessageHandler(
        filters.VIDEO | filters.Document.ALL,
        handle_file
    ))
    print("✅ Bot running!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
