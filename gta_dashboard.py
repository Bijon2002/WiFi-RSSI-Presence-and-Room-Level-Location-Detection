import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
import glob
import os
import random
import config
from logger import read_rssi
from detector import load_baseline, is_occupied
from db import log_event
from alert import send_alert
from fingerprint_match import build_model

# Apply dark theme
plt.style.use('dark_background')

def get_fingerprinted_rooms():
    rooms = []
    for filepath in glob.glob(f"{config.FINGERPRINT_DIR}/*.csv"):
        room = os.path.basename(filepath).replace(".csv", "")
        rooms.append(room)
    return sorted(list(set(rooms)))

rooms = get_fingerprinted_rooms()
if not rooms:
    print("\n[ERROR] No fingerprints found!")
    print("Please collect room fingerprints first by running:")
    print("  python fingerprint_collect.py kitchen")
    exit(1)

try:
    mean, std = load_baseline()
except FileNotFoundError:
    print("Baseline not found! Please run 'python main.py baseline' first.")
    exit(1)

model = build_model()
print(f"Loaded GTA Radar for rooms: {', '.join(rooms)}")

# Setup Polar Plot (Radar)
fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={'projection': 'polar'})
fig.canvas.manager.set_window_title("Vice City Wi-Fi Radar")

# GTA Vice City Colors
BG_COLOR = '#0a192f' # Deep dark blue/black
GRID_COLOR = '#ff007f' # Neon Pink
TEXT_COLOR = '#00ffff' # Neon Cyan
BLIP_COLOR = '#00ff00' # Neon Green

fig.patch.set_facecolor('black')
ax.set_facecolor(BG_COLOR)
ax.spines['polar'].set_color(GRID_COLOR)
ax.spines['polar'].set_linewidth(4)
ax.tick_params(colors=TEXT_COLOR)

# Remove the default radius circles to make it look cleaner
ax.set_yticklabels([])
ax.grid(color=GRID_COLOR, alpha=0.3, linestyle='--')

# Divide radar into pie sectors based on number of rooms
num_rooms = len(rooms)
theta_ticks = np.linspace(0, 2 * np.pi, num_rooms, endpoint=False)
ax.set_xticks(theta_ticks)
ax.set_xticklabels([]) # Hide default ticks

# Draw custom room labels in the middle of each sector
for i, label in enumerate([r.replace("_", " ").upper() for r in rooms]):
    angle = theta_ticks[i] + (np.pi / num_rooms)
    ax.text(angle, 1.15, label, ha='center', va='center', color=TEXT_COLOR, fontsize=14, fontweight='bold')

# Create the blip object (starts empty/hidden)
blip = ax.scatter([], [], c=BLIP_COLOR, s=400, marker='o', edgecolors='white', linewidths=2, zorder=10)

was_occupied_state = [False]

def update(frame):
    rssi = read_rssi()
    if rssi is None:
        blip.set_offsets(np.empty((0, 2))) # Hide blip
        return blip,
        
    occupied = is_occupied(rssi, mean, std)
    
    # Backend detector logic (DB + Telegram)
    was_occupied = was_occupied_state[0]
    if occupied and not was_occupied:
        log_event("occupancy_start", rssi)
        send_alert(f"Movement detected on the radar! RSSI={rssi}")
    elif not occupied and was_occupied:
        log_event("occupancy_end", rssi)
    was_occupied_state[0] = occupied
    
    # Radar visualization
    if occupied:
        predicted_room = model.predict([[rssi]])[0]
        room_index = rooms.index(predicted_room)
        
        # Calculate angle for the blip (somewhere inside the room's pie slice)
        base_angle = theta_ticks[room_index]
        angle = base_angle + (np.pi / num_rooms)
        
        # Add slight random jitter to radius and angle so the blip looks "alive"
        jitter_angle = random.uniform(-0.1, 0.1)
        radius = random.uniform(0.3, 0.9)
        
        # Update blip location (theta, r)
        blip.set_offsets(np.array([[angle + jitter_angle, radius]]))
        
        # Flashing effect
        if frame % 2 == 0:
            blip.set_alpha(1.0)
            ax.set_facecolor('#1a0033') # Flash background slightly purple
        else:
            blip.set_alpha(0.5)
            ax.set_facecolor(BG_COLOR)
    else:
        # Hide blip and reset background if no movement
        blip.set_offsets(np.empty((0, 2)))
        ax.set_facecolor(BG_COLOR)
        
    return blip,

print("Starting GTA Radar...")
# 500ms interval for a fast flashing radar effect
ani = FuncAnimation(fig, update, interval=500, cache_frame_data=False)
plt.tight_layout()
plt.show()
