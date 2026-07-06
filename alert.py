import subprocess
import requests
import config

import sys

def send_alert(message):
    try:
        print(f"[ALERT] {message}")
    except UnicodeEncodeError:
        # Fallback to ascii/console encoding with replacement characters
        encoding = sys.stdout.encoding or 'ascii'
        safe_msg = message.encode(encoding, errors='replace').decode(encoding)
        print(f"[ALERT] {safe_msg}")
    
    # Telegram (optional, works from anywhere)
    if config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
        try:
            requests.post(url, data={"chat_id": config.TELEGRAM_CHAT_ID, "text": message}, timeout=5)
        except Exception as e:
            print(f"[ERROR] Failed to send Telegram alert: {e}")
