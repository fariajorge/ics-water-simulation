from flask import Flask, request, jsonify
import threading
import time

app = Flask(__name__)

state = {
    "level_cm": 40.0,
    "pressure": 0.20,
    "pump_on": False,
    "s_low": 0,
    "s_medium": 0,
    "s_high": 0
}

def update_sensors():
    if state["level_cm"] > 20: state["s_low"] = 1
    else: state["s_low"] = 0

    if state["level_cm"] > 50: state["s_medium"] = 1
    else: state["s_medium"] = 0

    if state["level_cm"] > 80: state["s_high"] = 1
    else: state["s_high"] = 0

    state["pressure"] = round(state["level_cm"] * 0.005, 3)

def simulation_loop():
    while True:
        if state["pump_on"]:
            state["level_cm"] = min(100, state["level_cm"] + 0.5)
        else:
            state["level_cm"] = max(0, state["level_cm"] - 0.3)

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
