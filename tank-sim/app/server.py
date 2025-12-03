from flask import Flask, request, jsonify
import threading
import time

app = Flask(__name__)

# CONFIGURABLE PARAMETERS
MAX_NATURAL_LEVEL = 50.0    # Tank naturally stops rising at 50 cm
PUMP_MAX_RATE = 5           # cm per second at 100% power
LEAK_RATE = 0.5             # cm per second naturally leaking
MAX_LEVEL = 100.0           # Physical tank maximum

state = {
    "level_cm": 0.0,
    "pressure": 0.20,
    "pump_on": False,        # external enable (from Node-RED)
    "pump_power": 0.0,       # 0–100, set from dashboard
    "s_low": 0,
    "s_medium": 0,
    "s_high": 0
}

def update_sensors():
    lvl = state["level_cm"]
    state["s_low"] = 1 if lvl > 20 else 0
    state["s_medium"] = 1 if lvl > 50 else 0
    state["s_high"] = 1 if lvl > 80 else 0
    state["pressure"] = round(lvl * 0.005, 3)

def simulation_loop():
    while True:
        lvl = state["level_cm"]

        # 1) Natural leak always applies
        lvl -= LEAK_RATE

        # 2) Pump effect, scaled by pump_power (0–100)
        if state["pump_on"] and lvl < MAX_NATURAL_LEVEL:
            power_factor = max(0.0, min(1.0, state["pump_power"] / 100.0))
            lvl += PUMP_MAX_RATE * power_factor
            if lvl > MAX_NATURAL_LEVEL:
                lvl = MAX_NATURAL_LEVEL

        # 3) Physical constraints
        lvl = max(0.0, min(MAX_LEVEL, lvl))

        state["level_cm"] = lvl
        update_sensors()
        time.sleep(1)

@app.route("/state", methods=["GET"])
def get_state():
    return jsonify(state)

@app.route("/command", methods=["POST"])
def command():
    data = request.json or {}

    if "pump_on" in data:
        state["pump_on"] = bool(data["pump_on"])
        # If pump is turned off, force pump_power to 0
        if not state["pump_on"]:
            state["pump_power"] = 0.0

    if "pump_power" in data:
        try:
            p = float(data["pump_power"])
        except (TypeError, ValueError):
            p = 0.0
        p = max(0.0, min(100.0, p))
        state["pump_power"] = p

    return jsonify({
        "status": "ok",
        "pump_on": state["pump_on"],
        "pump_power": state["pump_power"]
    })

if __name__ == "__main__":
    thread = threading.Thread(target=simulation_loop, daemon=True)
    thread.start()
    app.run(host="0.0.0.0", port=5000)

