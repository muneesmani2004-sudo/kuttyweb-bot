import os
import requests
import logging
from pyrogram import Client, filters
from pyrogram.types import Message

# ══════════════════════════════════
# CONFIG
# ══════════════════════════════════
API_ID   = 35328597
API_HASH = "3751f8f4dce4805f4f62aa516375297b"
SESSION  = os.environ.get("SESSION_STRING", "")
DOOD_KEY = "559711b5fn9i7yrsq2o9fb"
DOOD_API = "https://doodapi.co/api"

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)

# ══════════════════════════════════
# DOODSTREAM
# ══════════════════════════════════
def dood_get_server():
    try:
        r = requests.get(f"{DOOD_API}/upload/server?key={DOOD_KEY}", timeout=15)
        d = r.json()
        if d.get("status") == 200:
            return d["result"]
    except Exception as e:
        logging.error(f"Server error: {e}")
    return None

def dood_upload(path, name):
    server = dood_get_server()
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
        logging.info(f"Dood: {d}")
        if d.get("status") == 200:
            files = d.get("files", [])
            if files:
                return files[0].get("filecode")
    except Exception as e:
        logging.error(f"Upload error: {e}")
    return None

def dood_account():
    try:
        r = requests.get(f"{DOOD_API}/account/info?key={DOOD_KEY}", timeout=10)
        return r.json()
    except:
        return None

# ══════════════════════════════════
# USER BOT
# ══════════════════════════════════
app = Client(
    "kuttyweb",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION
)

# .start command
@app.on_message(filters.me & filters.command(["start"], prefixes=[".", "!"]))
async def cmd_start(client, message):
    await message.reply(
        "🎬 KuttyWeb UserBot Active!\n\n"
        "📤 HOW TO USE:\n"
        "Send any video file here\n"
        "Bot auto uploads to Doodstream!\n\n"
        "✅ NO file size limit!\n"
        "✅ Works with any video!\n\n"
        "Commands:\n"
        ".start - This message\n"
        ".account - Storage info"
    )

# .account command
@app.on_message(filters.me & filters.command(["account"], prefixes=[".", "!"]))
async def cmd_account(client, message):
    data = dood_account()
    if data and data.get("status") == 200:
        res = data["result"]
        used = int(res.get("storage_used", 0)) / (1024**3)
        left = int(res.get("storage_left", 0)) / (1024**3)
        await message.reply(
            f"📊 Doodstream Account\n\n"
            f"Email: {res.get('email')}\n"
            f"Balance: ${res.get('balance','0')}\n"
            f"Used: {used:.2f} GB\n"
            f"Left: {left:.2f} GB"
        )
    else:
        await message.reply("❌ Could not get account info!")

# Handle video/document files
@app.on_message(filters.me & (filters.video | filters.document))
async def handle_media(client: Client, message: Message):
    media = message.video or message.document
    if not media:
        return

    # Only handle video documents
    mime = getattr(media, "mime_type", "") or ""
    if message.document and not mime.startswith("video"):
        return

    name = getattr(media, "file_name", None) or f"movie_{media.file_unique_id}.mp4"
    size_mb = round((media.file_size or 0) / (1024 * 1024), 1)
    size_gb = round(size_mb / 1024, 2)

    status = await message.reply(
        f"📥 Received: {name}\n"
        f"📦 Size: {size_mb} MB ({size_gb} GB)\n\n"
        f"⏳ Downloading from Telegram...\n"
        f"Please wait..."
    )

    path = f"/tmp/{name}"

    try:
        # Download file
        await client.download_media(message, file_name=path)

        await status.edit(
            f"📥 {name}\n"
            f"📦 {size_mb} MB\n\n"
            f"📤 Uploading to Doodstream...\n"
            f"Please wait, may take few minutes..."
        )

        # Upload to Doodstream
        code = dood_upload(path, name)

        if code:
            await status.edit(
                f"✅ Upload Successful!\n\n"
                f"🎬 {name}\n"
                f"📦 {size_mb} MB\n\n"
                f"▶️ Stream:\n"
                f"https://dood.watch/e/{code}\n\n"
                f"⬇️ Download:\n"
                f"https://dood.watch/d/{code}\n\n"
                f"Copy link → Admin Panel → Add Movie ✅"
            )
        else:
            await status.edit(
                "❌ Doodstream upload failed!\n"
                "Please try again."
            )

    except Exception as e:
        logging.error(f"Error: {e}")
        await status.edit(f"❌ Error: {str(e)}")
    finally:
        if os.path.exists(path):
            os.remove(path)

print("🤖 KuttyWeb UserBot starting...")
app.run()
