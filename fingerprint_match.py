import glob
import pandas as pd
import numpy as np
import os
from sklearn.neighbors import KNeighborsClassifier
import config
from logger import read_rssi

def build_model():
    X, y = [], []
    for filepath in glob.glob(f"{config.FINGERPRINT_DIR}/*.csv"):
        room = os.path.basename(filepath).replace(".csv", "")
        df = pd.read_csv(filepath, names=["timestamp", "rssi"])
        for rssi in df["rssi"]:
            X.append([rssi])
            y.append(room)
    model = KNeighborsClassifier(n_neighbors=5)
    model.fit(X, y)
    return model

def predict_room(model):
    rssi = read_rssi()
    if rssi is not None:
        return model.predict([[rssi]])[0]
    return None

if __name__ == "__main__":
    import time
    model = build_model()
    print("Localizing every 2s. Ctrl+C to stop.")
    while True:
        room = predict_room(model)
        if room:
            print(f"Predicted room: {room}")
        time.sleep(2)
