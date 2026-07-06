import subprocess
import re
import time
import csv
from datetime import datetime
import config

def read_rssi(interface=config.INTERFACE):
    """Return current RSSI (dBm, negative int) for the given interface. Windows version using netsh."""
    try:
        out = subprocess.check_output(["netsh", "wlan", "show", "interfaces"], stderr=subprocess.DEVNULL).decode(errors='ignore')
        match = re.search(r"Signal\s*:\s*(\d+)%", out)
        if match:
            quality = int(match.group(1))
            # approximation of dBm from quality %
            dbm = (quality / 2) - 100
            return int(dbm)
    except Exception as e:
        print(f"RSSI read error: {e}")
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
