import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.animation import FuncAnimation
import glob
import os
import config
from logger import read_rssi
from fingerprint_match import build_model

def get_fingerprinted_rooms():
    rooms = []
    # Using glob to find all CSV files in the fingerprints directory
    for filepath in glob.glob(f"{config.FINGERPRINT_DIR}/*.csv"):
        room = os.path.basename(filepath).replace(".csv", "")
        rooms.append(room)
    return sorted(list(set(rooms)))

rooms = get_fingerprinted_rooms()
if not rooms:
    print("\n[ERROR] No fingerprints found!")
    print("Please collect room fingerprints first by running:")
    print("  python fingerprint_collect.py kitchen")
    print("  python fingerprint_collect.py bedroom")
    exit(1)

model = build_model()
print(f"Loaded k-NN model for rooms: {', '.join(rooms)}")

fig, ax = plt.subplots(figsize=(10, 6))
ax.set_title("Live Floor Plan Localization", fontsize=16)
ax.axis('off')

# Layout logic: arrange room boxes side-by-side dynamically
room_patches = {}
x_offset = 0
for room in rooms:
    # Draw a 10x10 square for each room
    rect = Rectangle((x_offset, 0), 10, 10, edgecolor='black', facecolor='lightgray', linewidth=2)
    ax.add_patch(rect)
    # Add text label in the middle of the box
    ax.text(x_offset + 5, 5, room.replace("_", " ").upper(), ha='center', va='center', fontsize=12, fontweight='bold')
    room_patches[room] = rect
    x_offset += 12 # Space between rooms

ax.set_xlim(-2, x_offset)
ax.set_ylim(-2, 12)

# Text to display current live RSSI
status_text = ax.text(0, -1.5, 'Waiting for signal...', fontsize=12, color='blue')

def update(frame):
    rssi = read_rssi()
    if rssi is not None:
        # Predict which room we are in using k-NN model
        predicted_room = model.predict([[rssi]])[0]
        
        status_text.set_text(f"Live RSSI: {rssi} dBm")
        
        # Reset all rooms to gray
        for room, patch in room_patches.items():
            patch.set_facecolor('lightgray')
            
        # Highlight predicted room in green
        if predicted_room in room_patches:
            room_patches[predicted_room].set_facecolor('#aaffaa') # Light green
            
    return list(room_patches.values()) + [status_text]

print("Starting live floor plan visualization...")
# Update every 2 seconds to match predict_room logic
ani = FuncAnimation(fig, update, interval=2000, cache_frame_data=False)
plt.tight_layout()
plt.show()
