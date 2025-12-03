from flask import Flask, request, jsonify
import threading
import time

app = Flask(__name__)

# CONFIGURABLE PARAMETERS
MAX_NATURAL_LEVEL = 50       # Tank naturally stops rising at 50 cm
PUMP_RATE = 0.7              # Pump raises water level when below natural limit
LEAK_RATE = 0.2              # Natural leak always happening
MAX_LEVEL = 100              # Physical tank maximum

state = {
    "level_cm": 40.0,
    "pressure": 0.20,
    "pump_on": False,
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

        # Natural leak always applies
        lvl -= LEAK_RATE

        # Pump effect
        if state["pump_on"]:
            # Only fills up to MAX_NATURAL_LEVEL
            if lvl < MAX_NATURAL_LEVEL:
                lvl += PUMP_RATE
            else:
                lvl = MAX_NATURAL_LEVEL  # Clamp at natural fill limit

        # Physical constraints
        lvl = max(0, min(MAX_LEVEL, lvl))

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

