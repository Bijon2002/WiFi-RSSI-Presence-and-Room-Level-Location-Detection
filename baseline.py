import os
import numpy as np
import pandas as pd
import config
from logger import log_to_csv

def collect_baseline():
    os.makedirs(config.DATA_DIR, exist_ok=True)
    print(f"Collecting baseline for {config.BASELINE_DURATION}s. Keep the room EMPTY.")
    log_to_csv(config.BASELINE_FILE, config.BASELINE_DURATION)
    print("Baseline collection done.")

def compute_baseline_stats():
    df = pd.read_csv(config.BASELINE_FILE, names=["timestamp", "rssi"])
    mean, std = df["rssi"].mean(), df["rssi"].std()
    print(f"Baseline mean={mean:.2f} dBm, std={std:.2f}")
    return mean, std

if __name__ == "__main__":
    collect_baseline()
    compute_baseline_stats()
