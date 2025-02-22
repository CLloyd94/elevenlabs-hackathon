import argparse
import requests

def send_message(bot_token, chat_id, message):
    """Sends a message to a Telegram user via the bot."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, json=payload)
    return response.json()

def main():
    parser = argparse.ArgumentParser(
        description="Send a message to a specified Telegram user via a bot."
    )
    parser.add_argument("--chat_id", "-c", required=True, help="Target chat ID")
    parser.add_argument("--username", "-u", required=True, help="Target user name")
    parser.add_argument("--bot_token", "-b", required=True, help="Telegram bot token")
    parser.add_argument("--message", "-m", required=True, help="Message to send to the user")
    
    args = parser.parse_args()
    
    print(f"Sending message to {args.username} (ID: {args.chat_id})...")
    res = send_message(args.bot_token, args.chat_id, args.message)
    print("Success" if res.get('ok') else "Failed", res)

if __name__ == '__main__':
    main()