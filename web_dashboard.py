from flask import Flask, jsonify, render_template
import threading
import time
import math
import collections
import numpy as np
import os
import glob
from flask.json.provider import DefaultJSONProvider
from logger import read_rssi
from detector import load_baseline, is_occupied
import config
from db import log_event
from alert import send_alert

app = Flask(__name__)

class NumpyJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, (np.integer, np.floating)):
            return obj.item()
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif type(obj).__name__ in ('bool_', 'bool') and hasattr(obj, 'item'):
            return bool(obj)
        return super().default(obj)

app.json = NumpyJSONProvider(app)

# Load baseline
try:
    mean, std = load_baseline()
except FileNotFoundError:
    print("Baseline not found! Please run 'python main.py baseline' first.")
    exit(1)

# Try to build KNN model for room localization
model = None
rooms = []

def load_localization():
    global model, rooms
    try:
        from fingerprint_match import build_model
        rooms_list = sorted(list(set(
            os.path.basename(filepath).replace(".csv", "")
            for filepath in glob.glob(f"{config.FINGERPRINT_DIR}/*.csv")
        )))
        if rooms_list:
            rooms = rooms_list
            model = build_model()
            print(f"Loaded room-level classification model for: {rooms}")
        else:
            print("No fingerprints found. Presence detection only.")
    except Exception as e:
        print(f"Room localization model could not be loaded: {e}. Presence detection only.")

load_localization()

# State
rssi_history = collections.deque(maxlen=60)
current_state = {
    "rssi": None,
    "occupied": False,
    "num_people": 0,
    "predicted_room": None,
    "rooms": rooms,
    "people": [],
    "mean": float(mean),
    "std": float(std),
    "threshold": float(mean - config.THRESHOLD_STD * std),
    "history": []
}

last_occupied_state = False
last_alert_time = 0

def estimate_distance_cm(rssi):
    d_m = 10 ** ((-35 - rssi) / 25.0)
    return max(10, int(d_m * 100))

def sensor_loop():
    global last_occupied_state, last_alert_time, model, rooms
    while True:
        rssi = read_rssi()
        if rssi is None:
            time.sleep(config.SAMPLE_INTERVAL)
            continue
            
        rssi_history.append(rssi)
        occupied = is_occupied(rssi, mean, std)
        dist_cm = estimate_distance_cm(rssi)
        
        drop = mean - rssi
        if drop > 8:
            num_people = 3
        elif drop > 4:
            num_people = 2
        elif occupied:
            num_people = 1
        else:
            num_people = 0
            
        # Predict room if occupied
        predicted_room = None
        if occupied and model is not None:
            try:
                predicted_room = model.predict([[rssi]])[0]
            except Exception as e:
                print(f"KNN Prediction error: {e}")
                
        people_coords = []
        person_details = []
        if occupied:
            angles = [0, 45, -45, 90, -90]
            for i in range(num_people):
                angle_deg = angles[i % len(angles)]
                jitter = i * 20
                p_dist = dist_cm + jitter
                people_coords.append({
                    "id": f"P{i+1}",
                    "distance_cm": p_dist,
                    "angle_deg": angle_deg
                })
                person_details.append(f"P{i+1}: {p_dist} cm away")
                
            if not last_occupied_state:
                log_event("occupancy_start", rssi, predicted_room)
                
            if time.time() - last_alert_time > 5:
                room_str = f" in {predicted_room.replace('_', ' ').title()}" if predicted_room else ""
                alert_msg = f"🚨 {num_people} person(s) detected{room_str}!\n" + "\n".join(person_details)
                send_alert(alert_msg)
                last_alert_time = time.time()
        else:
            if last_occupied_state:
                log_event("occupancy_end", rssi)
                
        last_occupied_state = occupied
        
        # Update global state
        current_state["rssi"] = float(rssi) if rssi is not None else None
        current_state["occupied"] = bool(occupied)
        current_state["num_people"] = int(num_people)
        current_state["predicted_room"] = predicted_room
        current_state["rooms"] = rooms
        current_state["people"] = people_coords
        current_state["history"] = [float(x) for x in rssi_history]
        
        time.sleep(config.SAMPLE_INTERVAL)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/data")
def api_data():
    return jsonify(current_state)

@app.route("/api/events")
def api_events():
    try:
        from db import get_recent_events
        rows = get_recent_events(limit=10)
        events = []
        for r in rows:
            events.append({
                "id": r[0],
                "timestamp": r[1],
                "event_type": r[2],
                "rssi": r[3],
                "room": r[4]
            })
        return jsonify(events)
    except Exception as e:
        print(f"Error fetching recent events: {e}")
        return jsonify([])

if __name__ == "__main__":
    t = threading.Thread(target=sensor_loop, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=5000, debug=False)
