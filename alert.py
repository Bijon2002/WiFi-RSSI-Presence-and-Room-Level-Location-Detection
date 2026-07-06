import subprocess
import requests
import config

def send_alert(message):
    # Desktop notification (Windows)
    try:
        subprocess.run(["powershell", "-Command", f"Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.MessageBox]::Show('{message}', 'WiFi Tracker')"], creationflags=subprocess.CREATE_NO_WINDOW)
    except Exception:
        pass
    
    # Telegram (optional, works from anywhere)
    if config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": config.TELEGRAM_CHAT_ID, "text": message})
