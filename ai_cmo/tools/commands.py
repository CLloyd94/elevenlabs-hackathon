import subprocess
import sys
import os
from dotenv import load_dotenv

load_dotenv()

# 1. Send message to telegram user
TARGET_CHAT_ID = os.getenv("TARGET_CHAT_ID")
TARGET_USER_NAME = os.getenv("TARGET_USER_NAME")
BOT_TOKEN = os.getenv("BOT_TOKEN")
MESSAGE = "Hello, this is a test message!"

# telegram_script = f'python3 telegram.py --chat_id {TARGET_CHAT_ID} --username {TARGET_USER_NAME} --bot_token {BOT_TOKEN} --message "{MESSAGE}"'
telegram_script = [
    "python3",
    "telegram_message_sender.py",
    "--chat_id", TARGET_CHAT_ID,
    "--username", TARGET_USER_NAME,
    "--bot_token", BOT_TOKEN,
    "--message", MESSAGE
]
# subprocess.run(telegram_script, stdout=sys.stdout, stderr=sys.stderr)


# 2. Upload video to Meta's Marketing API
AD_ACCOUNT_ID = os.getenv("AD_ACCOUNT_ID")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
REMOTE_FILE_PATH = "https://v3.fal.media/files/lion/ucDvw52soqabLG6ePoS9r_output.mp4"

# We can set the following
TITLE = "TEST"
DESCRIPTION = "TEST"
FILE_NAME="something.mp4"

ads_video_upload_command = [
    "python3", "ads_video_upload.py",
    "--ad_account_id", AD_ACCOUNT_ID,
    "--access_token", ACCESS_TOKEN,
    "--remote_file_path", REMOTE_FILE_PATH,
    "--file_name", FILE_NAME,    
    "--title", TITLE,
    "--description", DESCRIPTION
]

# upload_video = subprocess.run(ads_video_upload_command, stdout=sys.stdout, stderr=sys.stderr)
