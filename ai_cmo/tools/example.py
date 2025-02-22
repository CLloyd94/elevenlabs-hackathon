import os
from ads_video_upload import download_file, upload_ads_video
from telegram_message_sender import send_message

################################################################
# Ads Video Upload
################################################################

# From ENV
AD_ACCOUNT_ID = os.getenv("AD_ACCOUNT_ID")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

# We can set the following
TITLE = "TEST"
DESCRIPTION = "TEST"
FILE_NAME="something.mp4"
REMOTE_FILE_PATH = "https://v3.fal.media/files/lion/ucDvw52soqabLG6ePoS9r_output.mp4"

# Copy the following
local_file_path = f"./{FILE_NAME}"
download_file(REMOTE_FILE_PATH, FILE_NAME)
vid_id = upload_ads_video(
    AD_ACCOUNT_ID,
    local_file_path,
    ACCESS_TOKEN,
    title=TITLE,
    description=DESCRIPTION
)
if vid_id:
    print(f"Video uploaded successfully! Video ID: {vid_id}")
else:
    print("Video upload failed.")


################################################################
# Telegram
################################################################

# ENV
TARGET_CHAT_ID = os.getenv("TARGET_CHAT_ID")
TARGET_USER_NAME = os.getenv("TARGET_USER_NAME")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# CHANGE THIS
MESSAGE = "Hello, this is a test message!"

send_message(BOT_TOKEN, TARGET_CHAT_ID, MESSAGE)