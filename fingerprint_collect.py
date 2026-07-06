import os
import config
from logger import log_to_csv

def collect_fingerprint(room_name, duration=120):
    os.makedirs(config.FINGERPRINT_DIR, exist_ok=True)
    filepath = f"{config.FINGERPRINT_DIR}/{room_name}.csv"
    print(f"Recording fingerprint for '{room_name}' — stay in that room for {duration}s.")
    log_to_csv(filepath, duration)
    print(f"Saved: {filepath}")

if __name__ == "__main__":
    import sys
    room = sys.argv[1] if len(sys.argv) > 1 else input("Room name: ")
    collect_fingerprint(room)
