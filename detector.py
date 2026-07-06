import time
import pandas as pd
import config
from logger import read_rssi
from db import log_event
from alert import send_alert

def load_baseline():
    df = pd.read_csv(config.BASELINE_FILE, names=["timestamp", "rssi"])
    return df["rssi"].mean(), df["rssi"].std()

def is_occupied(live_rssi, mean, std, k=config.THRESHOLD_STD):
    return abs(live_rssi - mean) > k * std

def run_detector():
    mean, std = load_baseline()
    print(f"Monitoring... baseline mean={mean:.2f}, std={std:.2f}")
    was_occupied = False
    while True:
        rssi = read_rssi()
        if rssi is not None:
            occupied = is_occupied(rssi, mean, std)
            if occupied and not was_occupied:
                print(f"[ALERT] Motion/occupancy detected, RSSI={rssi}")
                log_event("occupancy_start", rssi)
                send_alert(f"Motion detected at home. RSSI={rssi}")
            elif not occupied and was_occupied:
                log_event("occupancy_end", rssi)
            was_occupied = occupied
        time.sleep(config.SAMPLE_INTERVAL)

if __name__ == "__main__":
    run_detector()
