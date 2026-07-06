import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import config
from logger import read_rssi
from detector import load_baseline
import collections

try:
    mean, std = load_baseline()
except FileNotFoundError:
    print("Baseline not found! Please run 'python main.py baseline' first.")
    exit(1)

print(f"Loaded baseline: mean={mean:.2f}, std={std:.2f}")

# Keep the last 60 data points (approx 60 seconds)
MAX_POINTS = 60
rssi_data = collections.deque(maxlen=MAX_POINTS)

fig, ax = plt.subplots(figsize=(10, 6))
line, = ax.plot([], [], lw=2, color='blue', label='Live RSSI')

# Draw baseline and thresholds
ax.axhline(y=mean, color='green', linestyle='--', label='Baseline Mean')
threshold_lower = mean - config.THRESHOLD_STD * std
threshold_upper = mean + config.THRESHOLD_STD * std
ax.axhline(y=threshold_lower, color='red', linestyle=':', label='Detection Threshold')
ax.axhline(y=threshold_upper, color='red', linestyle=':')

ax.set_xlim(0, MAX_POINTS)
ax.set_ylim(mean - 10, mean + 10)
ax.set_title("Live Wi-Fi RSSI (Movement Detection)")
ax.set_ylabel("RSSI (dBm)")
ax.set_xlabel("Time (seconds ago)")
ax.legend(loc='upper right')

# Text indicator for occupancy
status_text = ax.text(0.02, 0.95, '', transform=ax.transAxes, fontsize=14, fontweight='bold')

def update(frame):
    rssi = read_rssi()
    if rssi is not None:
        rssi_data.append(rssi)
        
        # X-axis is fixed 0 to MAX_POINTS, we just plot the deque
        x_data = list(range(len(rssi_data)))
        line.set_data(x_data, list(rssi_data))
        
        # Adjust Y axis dynamically if needed
        current_min = min(rssi_data)
        current_max = max(rssi_data)
        if current_min < ax.get_ylim()[0] or current_max > ax.get_ylim()[1]:
            ax.set_ylim(current_min - 5, current_max + 5)
            
        # Check occupancy
        if abs(rssi - mean) > config.THRESHOLD_STD * std:
            ax.set_facecolor('#ffcccc') # Light red background
            status_text.set_text('STATUS: MOVEMENT DETECTED')
            status_text.set_color('red')
        else:
            ax.set_facecolor('white')
            status_text.set_text('STATUS: Empty / Still')
            status_text.set_color('green')
            
    return line, status_text

print("Starting live visualization...")
ani = FuncAnimation(fig, update, interval=config.SAMPLE_INTERVAL * 1000, cache_frame_data=False)
plt.tight_layout()
plt.show()
