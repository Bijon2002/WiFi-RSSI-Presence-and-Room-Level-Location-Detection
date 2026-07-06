import subprocess
import re
import time
import csv
import threading
from datetime import datetime
import config

# --- Windows Cache Buster ---
# Windows caches Wi-Fi signals to save battery and doesn't update them unless forced.
# This background thread constantly forces Windows to rescan so the radar sees real movement!
def force_wifi_scan():
    while True:
        try:
            subprocess.run(["netsh", "wlan", "show", "networks", "mode=bssid"], 
                           capture_output=True, 
                           creationflags=subprocess.CREATE_NO_WINDOW)
        except:
            pass
        time.sleep(2)

scan_thread = threading.Thread(target=force_wifi_scan, daemon=True)
scan_thread.start()
# ----------------------------

def read_rssi(interface=config.INTERFACE):
    """Return current RSSI (dBm, negative int) for the given interface. Windows version using netsh."""
    try:
        out = subprocess.check_output(
            ["netsh", "wlan", "show", "interfaces"], 
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW
        ).decode(errors='ignore')
        
        match = re.search(r"Signal\s*:\s*(\d+)%", out)
        if match:
            quality = int(match.group(1))
            dbm = (quality / 2) - 100
            return int(dbm)
    except Exception as e:
        # Ignore Ctrl+C exit codes
        pass
    return None

def log_to_csv(filepath, duration_seconds, interval=config.SAMPLE_INTERVAL):
    """Continuously sample RSSI and append to CSV for `duration_seconds`."""
    end_time = time.time() + duration_seconds
    with open(filepath, "a", newline="") as f:
        writer = csv.writer(f)
        while time.time() < end_time:
            rssi = read_rssi()
            if rssi is not None:
                writer.writerow([datetime.now().isoformat(), rssi])
            f.flush()
            time.sleep(interval)

if __name__ == "__main__":
    # quick manual test: print RSSI every second
    while True:
        print(read_rssi())
        time.sleep(1)
