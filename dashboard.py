import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.animation import FuncAnimation
import collections
import config
from logger import read_rssi
from detector import load_baseline, is_occupied
from db import log_event
from alert import send_alert
import time
import math

# Load baseline
try:
    mean, std = load_baseline()
except FileNotFoundError:
    print("Baseline not found! Please run 'python main.py baseline' first.")
    exit(1)

print(f"Loaded baseline: mean={mean:.2f}, std={std:.2f}")

def estimate_distance_cm(rssi):
    # Free space path loss approximation
    # Assuming -35 dBm at 1 meter, path loss exponent n=2.5
    d_m = 10 ** ((-35 - rssi) / 25.0)
    return max(10, int(d_m * 100))

# Setup Dashboard UI
fig, (ax_graph, ax_radar) = plt.subplots(1, 2, figsize=(15, 6))
fig.suptitle("Wi-Fi Tracker: Whole House Radar", fontsize=18, fontweight='bold')

# --- Left Panel: 1D Graph ---
MAX_POINTS = 60
rssi_data = collections.deque(maxlen=MAX_POINTS)
line, = ax_graph.plot([], [], lw=2, color='blue', label='Live RSSI')
ax_graph.axhline(y=mean, color='green', linestyle='--', label='Baseline Mean')
threshold_lower = mean - config.THRESHOLD_STD * std
threshold_upper = mean + config.THRESHOLD_STD * std
ax_graph.axhline(y=threshold_lower, color='red', linestyle=':', label='Threshold')
ax_graph.axhline(y=threshold_upper, color='red', linestyle=':')
ax_graph.set_xlim(0, MAX_POINTS)
ax_graph.set_ylim(mean - 10, mean + 10)
ax_graph.set_title("Live Signal & Detection")
ax_graph.set_ylabel("RSSI (dBm)")
ax_graph.set_xlabel("Time (seconds ago)")
ax_graph.legend(loc='upper right')
status_text = ax_graph.text(0.02, 0.95, '', transform=ax_graph.transAxes, fontsize=12, fontweight='bold')

# --- Right Panel: Radar ---
ax_radar.set_title("Estimated Distance from Router")
ax_radar.set_xlim(-1000, 1000)
ax_radar.set_ylim(-1000, 1000)
ax_radar.set_aspect('equal')
ax_radar.axis('off')

# Draw Router
router_circle = Circle((0, 0), 50, color='black', label='Router')
ax_radar.add_patch(router_circle)
ax_radar.text(0, -100, 'ROUTER', ha='center', va='center', fontweight='bold')

# Draw Rings
for r in [200, 400, 600, 800]:
    ring = Circle((0, 0), r, color='gray', fill=False, linestyle='--')
    ax_radar.add_patch(ring)
    ax_radar.text(0, r + 30, f'{r}cm', ha='center', color='gray')

person_dot, = ax_radar.plot([], [], 'ro', markersize=15, label='Person')
radar_text = ax_radar.text(0, -900, 'Waiting for signal...', ha='center', fontsize=12, color='blue')

# --- Global State for Detector ---
last_occupied_state = False
last_alert_time = 0

def update(frame):
    global last_occupied_state, last_alert_time
    rssi = read_rssi()
    if rssi is None:
        return line, status_text, person_dot, radar_text
        
    rssi_data.append(rssi)
    
    # 1. Update Graph
    line.set_data(list(range(len(rssi_data))), list(rssi_data))
    current_min, current_max = min(rssi_data), max(rssi_data)
    if current_min < ax_graph.get_ylim()[0] or current_max > ax_graph.get_ylim()[1]:
        ax_graph.set_ylim(current_min - 5, current_max + 5)
        
    # 2. Detector Logic
    occupied = is_occupied(rssi, mean, std)
    dist_cm = estimate_distance_cm(rssi)
    
    # Multi-person estimation based on signal drop
    drop = mean - rssi
    if drop > 8:
        num_people = 3
    elif drop > 4:
        num_people = 2
    else:
        num_people = 1
    
    if occupied:
        msg = f"{num_people} person(s) moving inside the house! (~{dist_cm} cm away)"
        status_text.set_text(msg)
        status_text.set_color('red')
        ax_graph.set_facecolor('#ffcccc')
        
        # Draw multiple dots
        angles = [0, 45, -45]
        xs = []
        ys = []
        person_details = []
        for i in range(num_people):
            angle_deg = angles[i % len(angles)]
            angle_rad = math.radians(90 + angle_deg)
            jitter = i * 20
            p_dist = dist_cm + jitter
            xs.append(p_dist * math.cos(angle_rad))
            ys.append(p_dist * math.sin(angle_rad))
            person_details.append(f"P{i+1}: {p_dist} cm away (Angle: {angle_deg}°)")
            
        person_dot.set_data(xs, ys)
        radar_text.set_text(f'{num_people} person(s) detected')
        radar_text.set_color('red')
    else:
        status_text.set_text('House is Empty / Still')
        status_text.set_color('green')
        ax_graph.set_facecolor('white')
        person_dot.set_data([], [])
        radar_text.set_text('No movement detected')
        radar_text.set_color('green')
        
    # Background logic for alerts (Send continuously while occupied)
    if occupied:
        if not last_occupied_state:
            log_event("House", "Movement Started", rssi)
        
        # Send an alert every 5 seconds while movement continues
        if time.time() - last_alert_time > 5:
            alert_msg = f"🚨 {num_people} person(s) detected!\n" + "\n".join(person_details)
            send_alert(alert_msg)
            last_alert_time = time.time()
    elif not occupied and last_occupied_state:
        log_event("House", "Movement Stopped", rssi)
        
    last_occupied_state = occupied
    
    return line, status_text, person_dot, radar_text

print("Starting Whole House Radar...")
ani = FuncAnimation(fig, update, interval=config.SAMPLE_INTERVAL * 1000, cache_frame_data=False)
plt.tight_layout()
plt.show()
