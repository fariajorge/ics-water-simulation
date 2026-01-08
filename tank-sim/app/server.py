from flask import Flask, request, jsonify
import threading
import time

app = Flask(__name__)

# CONFIGURABLE PARAMETERS
PUMP_MAX_RATE = 5.0         # cm per second at 100% power
LEAK_RATE = 0.5             # cm per second, default leak
MAX_LEVEL = 100.0           # Physical tank maximum
DEFAULT_TARGET_CM = 50.0    # default target level (cm)

state = {
    "level_cm": 0.0,
    "pressure": 0.20,
    "pump_on": False,         # external enable (from Node-RED)
    "pump_power": 0.0,        # 0–100, set from dashboard
    "s_low": 0,
    "s_medium": 0,
    "s_high": 0,
    "leak_rate": LEAK_RATE,          # cm per second, adjustable at runtime
    "target_cm": DEFAULT_TARGET_CM,  # cm, adjustable at runtime
}

def update_sensors():
    lvl = float(state["level_cm"])
    state["s_low"] = 1 if lvl > 20 else 0
    state["s_medium"] = 1 if lvl > 50 else 0
    state["s_high"] = 1 if lvl > 80 else 0
    state["pressure"] = round(lvl * 0.005, 3)

def simulation_loop():
    while True:
        lvl = float(state["level_cm"])

        # 1) Natural leak always applies (runtime adjustable)
        leak = float(state.get("leak_rate", LEAK_RATE))
        lvl -= leak

        # 2) Pump effect, scaled by pump_power (0–100), capped by target_cm
        target = float(state.get("target_cm", DEFAULT_TARGET_CM))

        if state["pump_on"] and lvl < target:
            power_factor = max(0.0, min(1.0, float(state["pump_power"]) / 100.0))
            lvl += PUMP_MAX_RATE * power_factor
            if lvl > target:
                lvl = target

        # 3) Physical constraints
        lvl = max(0.0, min(MAX_LEVEL, lvl))
        
        # HARD SAFETY: physical tank full -> force pump OFF
        if lvl >= MAX_LEVEL:
            state["pump_on"] = False
            state["pump_power"] = 0.0

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

    # Adjustable leak rate
    if "leak_rate" in data:
        try:
            lr = float(data["leak_rate"])
        except (TypeError, ValueError):
            lr = LEAK_RATE
        lr = max(0.0, min(10.0, lr))  # clamp
        state["leak_rate"] = lr

    # Adjustable target level
    if "target_cm" in data:
        try:
            t = float(data["target_cm"])
        except (TypeError, ValueError):
            t = DEFAULT_TARGET_CM
        t = max(0.0, min(MAX_LEVEL, t))  # clamp to physical limits
        state["target_cm"] = t

    return jsonify({
        "status": "ok",
        "pump_on": state["pump_on"],
        "pump_power": state["pump_power"],
        "leak_rate": state.get("leak_rate", LEAK_RATE),
        "target_cm": state.get("target_cm", DEFAULT_TARGET_CM),
    })

if __name__ == "__main__":
    thread = threading.Thread(target=simulation_loop, daemon=True)
    thread.start()
    app.run(host="0.0.0.0", port=5000)

