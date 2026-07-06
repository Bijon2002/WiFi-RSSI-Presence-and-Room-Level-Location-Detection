import time
import config
from logger import read_rssi
from detector import load_baseline, is_occupied

try:
    mean, std = load_baseline()
except FileNotFoundError:
    print("Baseline not found! Please run 'python main.py baseline' first.")
    exit(1)

print("=====================================================")
print(f" Wi-Fi Motion Radar (Terminal Edition)")
print(f" Baseline loaded: Mean={mean:.2f}, Std={std:.2f}")
print(" Watching for movement... (Press Ctrl+C to stop)")
print("=====================================================")

while True:
    rssi = read_rssi()
    if rssi is None:
        time.sleep(1)
        continue
        
    occupied = is_occupied(rssi, mean, std)
    
    # Create an ASCII visual bar
    # RSSI is usually between -30 (strong) and -90 (weak)
    bar_length = max(0, rssi + 100) 
    
    if occupied:
        bar = "█" * bar_length
        status = "[ !!! MOVEMENT DETECTED !!! ]"
    else:
        bar = "▒" * bar_length
        status = "[ Still ]"
        
    # Print the line dynamically in the terminal
    print(f"\rRSSI: {rssi:3d} dBm | {status:29s} | {bar.ljust(80)}", end="", flush=True)
    time.sleep(config.SAMPLE_INTERVAL)
