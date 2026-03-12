# KuttyWeb Movie Uploader Bot 🎬

Upload movies from Telegram directly to Doodstream!

## How It Works
1. Send movie file to bot
2. Bot uploads to Doodstream automatically
3. Get stream + download links instantly
4. Paste in KuttyWeb Admin Panel ✅

## Deploy on Railway (Free)

### Step 1 - Upload to GitHub
- Create new GitHub repo named: `kuttyweb-bot`
- Upload these 3 files:
  - bot.py
  - requirements.txt
  - Procfile

### Step 2 - Deploy on Railway
- Go to railway.app
- Sign in with GitHub
- Click "New Project"
- Click "Deploy from GitHub repo"
- Select `kuttyweb-bot` repo
- Click Deploy ✅

### Step 3 - Add Environment Variable
- In Railway → your project → Variables
- Add: `ADMIN_ID` = your Telegram user ID
- Get your ID from @userinfobot on Telegram

### Step 4 - Start Bot
- Railway auto starts the bot
- Open Telegram → your bot
- Send /start ✅

## Bot Commands
- `/start` - Welcome message
- `/account` - Check Doodstream storage
- `/help` - Help guide
- Send any video file → auto upload!
- Send any URL → remote upload!

## Config
- BOT_TOKEN: Already set in bot.py
- DOOD_API_KEY: Already set in bot.py
- ADMIN_ID: Set in Railway environment variables
