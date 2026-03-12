import os
import time
import requests
import logging

# ══════════════════════════════════
# CONFIG
# ══════════════════════════════════
BOT_TOKEN = "8280311962:AAEjSIObBnkGMjogBvDVjwScqaMtIqM1EbM"
DOOD_KEY  = "559711b5fn9i7yrsq2o9fb"
DOOD_API  = "https://doodapi.co/api"
TG_API    = f"https://api.telegram.org/bot{BOT_TOKEN}"
TG_FILE   = f"https://api.telegram.org/file/bot{BOT_TOKEN}"
ADMIN_ID  = int(os.environ.get("ADMIN_ID", "0"))

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)

# ══════════════════════════════════
# TELEGRAM HELPERS
# ══════════════════════════════════
def tg_send(chat_id, text):
    requests.post(f"{TG_API}/sendMessage", json={"chat_id": chat_id, "text": text}, timeout=10)

def tg_edit(chat_id, msg_id, text):
    requests.post(f"{TG_API}/editMessageText", json={"chat_id": chat_id, "message_id": msg_id, "text": text}, timeout=10)

def tg_send_and_get_id(chat_id, text):
    r = requests.post(f"{TG_API}/sendMessage", json={"chat_id": chat_id, "text": text}, timeout=10)
    d = r.json()
    if d.get("ok"):
        return d["result"]["message_id"]
    return None

def get_file_url(file_id):
    r = requests.get(f"{TG_API}/getFile", params={"file_id": file_id}, timeout=10)
    d = r.json()
    if d.get("ok"):
        return f"{TG_FILE}/{d['result']['file_path']}"
    return None

# ══════════════════════════════════
# DOODSTREAM HELPERS
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
# PROCESS UPDATE
# ══════════════════════════════════
def process_update(update):
    msg = update.get("message")
    if not msg:
        return

    chat_id = msg["chat"]["id"]
    user_id = msg["from"]["id"]

    # Check admin
    if ADMIN_ID != 0 and user_id != ADMIN_ID:
        tg_send(chat_id, "⛔ Access denied!")
        return

    text = msg.get("text", "")

    # /start command
    if text == "/start":
        tg_send(chat_id,
            "🎬 KuttyWeb Uploader Bot\n\n"
            "Send any movie/video file\n"
            "I upload it to Doodstream!\n\n"
            "/start - This message\n"
            "/account - Storage info"
        )
        return

    # /account command
    if text == "/account":
        data = dood_account()
        if data and data.get("status") == 200:
            res = data["result"]
            used = int(res.get("storage_used", 0)) / (1024**3)
            left = int(res.get("storage_left", 0)) / (1024**3)
            tg_send(chat_id,
                f"📊 Doodstream Account\n\n"
                f"Email: {res.get('email')}\n"
                f"Balance: ${res.get('balance','0')}\n"
                f"Used: {used:.2f} GB\n"
                f"Left: {left:.2f} GB"
            )
        else:
            tg_send(chat_id, "❌ Could not get account info!")
        return

    # Handle video/document
    video = msg.get("video") or msg.get("document")
    if not video:
        tg_send(chat_id, "📤 Send a movie/video file to upload!")
        return

    name = video.get("file_name") or f"movie_{video['file_unique_id']}.mp4"
    size_mb = round((video.get("file_size") or 0) / (1024*1024), 1)
    file_id = video["file_id"]

    msg_id = tg_send_and_get_id(chat_id,
        f"📥 Received: {name}\n"
        f"Size: {size_mb} MB\n\n"
        f"⏳ Getting download link..."
    )

    # Get file URL from Telegram
    file_url = get_file_url(file_id)

    if not file_url:
        tg_edit(chat_id, msg_id, "❌ Could not get file from Telegram!\nFile may be too large (>20MB limit).\n\nTip: Upload to Doodstream directly from their website.")
        return

    tg_edit(chat_id, msg_id,
        f"📥 {name} ({size_mb} MB)\n\n"
        f"⬇️ Downloading file...\nPlease wait..."
    )

    # Download file
    path = f"/tmp/{name}"
    try:
        r = requests.get(file_url, timeout=300, stream=True)
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    except Exception as e:
        tg_edit(chat_id, msg_id, f"❌ Download failed: {e}")
        return

    tg_edit(chat_id, msg_id,
        f"📥 {name} ({size_mb} MB)\n\n"
        f"📤 Uploading to Doodstream...\n"
        f"Please wait, this may take a few minutes..."
    )

    # Upload to Doodstream
    code = dood_upload(path, name)

    # Cleanup
    if os.path.exists(path):
        os.remove(path)

    if code:
        tg_edit(chat_id, msg_id,
            f"✅ Upload Successful!\n\n"
            f"🎬 {name}\n"
            f"📦 {size_mb} MB\n\n"
            f"▶️ Stream:\nhttps://dood.watch/e/{code}\n\n"
            f"⬇️ Download:\nhttps://dood.watch/d/{code}\n\n"
            f"Copy link → Admin Panel → Add Movie ✅"
        )
    else:
        tg_edit(chat_id, msg_id, "❌ Upload to Doodstream failed!\nPlease try again.")

# ══════════════════════════════════
# MAIN POLLING LOOP
# ══════════════════════════════════
def main():
    print("🤖 KuttyWeb Bot starting...")
    offset = 0
    while True:
        try:
            r = requests.get(
                f"{TG_API}/getUpdates",
                params={"offset": offset, "timeout": 30},
                timeout=35
            )
            updates = r.json().get("result", [])
            for update in updates:
                offset = update["update_id"] + 1
                try:
                    process_update(update)
                except Exception as e:
                    logging.error(f"Update error: {e}")
        except Exception as e:
            logging.error(f"Poll error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
