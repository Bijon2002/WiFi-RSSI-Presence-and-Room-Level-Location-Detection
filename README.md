# WiFi RSSI Presence & Room-Level Location Detection

This project uses your laptop's WiFi interface to detect presence (motion/occupancy) and approximate room-level location based on RSSI (Received Signal Strength Indicator) from a router, without requiring extra hardware.

## Prerequisites

- Python 3.7+
- Windows (via `netsh`) supported out of the box in this implementation. 
- (Linux/Mac users will need to adapt `logger.py` to use `iwconfig` or `airport`).

## Setup

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Settings:**
   Open `config.py` and ensure the settings match your environment:
   - `INTERFACE`: Your Wi-Fi interface name (e.g., `"Wi-Fi"` on Windows, `"wlan0"` on Linux).
   - `THRESHOLD_STD`: Detection sensitivity (lower = more sensitive, but more false positives).
   - *Optional:* Add `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` for Telegram alerts.

## Execution Steps

### Phase 1: Baseline Collection
Run this while the room is empty for ~10 minutes. This creates a "normal" signal fingerprint for the empty room.
```bash
python main.py baseline
```

### Phase 2 & 3: Live Occupancy Detection
Run this to detect presence. Walk around and confirm if alerts fire correctly.
```bash
python main.py detect
```
*Note: If you experience false positives/negatives, tune the `THRESHOLD_STD` in `config.py`.*

### Phase 4: Room-Level Fingerprinting (Optional)
Collect RSSI fingerprints for specific rooms to enable room-level localization.

1. **Collect Data for Each Room:**
   Stand the laptop at a fixed point in a room for ~2 minutes.
   ```bash
   python fingerprint_collect.py kitchen
   python fingerprint_collect.py bedroom
   python fingerprint_collect.py living_room
   ```

2. **Match & Localize:**
   Run the k-NN model to predict the current room based on live RSSI.
   ```bash
   python fingerprint_match.py
   ```

### Phase 5: Alerts (Optional)
To receive Telegram notifications when motion is detected:
1. Message `@BotFather` on Telegram to create a bot and get the token.
2. Send a message to your new bot.
3. Visit `https://api.telegram.org/bot<TOKEN>/getUpdates` to find your `chat_id`.
4. Update `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `config.py`.

## Known Limitations

- Single router + laptop gives presence/motion detection reliably, but only approximate room-level location via fingerprinting.
- No identity detection with RSSI alone.
- Other 2.4GHz devices (microwaves, Bluetooth) add noise — recollect the baseline if the environment changes.
- Adjacent open-plan rooms will confuse the k-NN model. A second AP or BLE beacon per room is needed for real separation.
