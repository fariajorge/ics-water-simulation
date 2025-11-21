from flask import Flask, request, jsonify
import threading
import time

app = Flask(__name__)

# CONFIGURABLE PARAMETERS
TARGET_LEVEL = 50.0        # Desired level in cm
MAX_LEVEL = 100.0          # Physical max level in cm

PUMP_MAX_RATE = 0.8        # cm per second at full power
RAMP_RANGE = 20.0          # below target, where power ramps (cm)
LEAK_RATE = 0.2            # cm per second naturally leaking

state = {
    "level_cm": 40.0,
    "pressure": 0.20,
    "pump_on": False,      # external enable (from Node-RED)
    "pump_power": 0.0,     # 0.0–1.0 how hard the pump is working
    "s_low": 0,
    "s_medium": 0,
    "s_high": 0
}

def update_sensors():
    lvl = state["level_cm"]

    # Digital sensors based on level
    state["s_low"] = 1 if lvl > 20 else 0
    state["s_medium"] = 1 if lvl > 50 else 0
    state["s_high"] = 1 if lvl > 80 else 0

    # Simple pressure model from level
    state["pressure"] = round(lvl * 0.005, 3)

def simulation_loop():
    while True:
        lvl = state["level_cm"]

        # 1) Natural leak always happening
        lvl -= LEAK_RATE

        # 2) Compute pump power if enabled
        pump_power = 0.0
        if state["pump_on"]:
            error = TARGET_LEVEL - lvl

            if error > 0:
                # Below target: ramp power from 0..1 depending on distance
                pump_power = error / RAMP_RANGE
                if pump_power > 1.0:
                    pump_power = 1.0
            else:
                # At or above target: no pumping needed
                pump_power = 0.0

        state["pump_power"] = round(pump_power, 3)

        # 3) Pump effect on level
        lvl += PUMP_MAX_RATE * pump_power

        # 4) Physical constraints
        lvl = max(0.0, min(MAX_LEVEL, lvl))

        state["level_cm"] = lvl
        update_sensors()

        time.sleep(1)

@app.route("/state", methods=["GET"])
def get_state():
    return jsonify(state)

@app.route("/command", methods=["POST"])
def command():
    data = request.json
    if "pump_on" in data:
        state["pump_on"] = bool(data["pump_on"])
    return jsonify({"status": "ok", "pump_on": state["pump_on"]})

if __name__ == "__main__":
    thread = threading.Thread(target=simulation_loop, daemon=True)
    thread.start()
    app.run(host="0.0.0.0", port=5000)

