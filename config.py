import os
from dotenv import load_dotenv

load_dotenv()

INTERFACE = "Wi-Fi"  # your WiFi interface name
SAMPLE_INTERVAL = 1  # seconds between RSSI samples
BASELINE_DURATION = 30  # 30 second baseline collection for testing
THRESHOLD_STD = 2.5  # sensitivity: lower = more sensitive, more false positives
DATA_DIR = "data"
BASELINE_FILE = f"{DATA_DIR}/baseline_rssi.csv"
DB_FILE = f"{DATA_DIR}/events.db"
FINGERPRINT_DIR = f"{DATA_DIR}/fingerprints"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # fill in if using Telegram alerts
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
