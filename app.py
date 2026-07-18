from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import os
import random
from datetime import datetime

app = Flask(__name__)
app.secret_key = "mine_safety_secret_key_2026"

# ---------------------------------------------------
# Demo login credentials
# ---------------------------------------------------
USERS = {
    "admin": "admin123",
    "worker": "worker123",
}
ADMIN_USERS = {"admin"}

# ---------------------------------------------------
# Worker data (synthetic — replace with real sensor/GPS data if available)
# lat/lng are placed around a sample mine site for map display
# ---------------------------------------------------
WORKERS = {
    "W001": {"name": "Ravi Kumar", "zone": "Tunnel A", "lat": 23.3441, "lng": 85.3096},
    "W002": {"name": "Suresh Babu", "zone": "Tunnel B", "lat": 23.3455, "lng": 85.3112},
    "W003": {"name": "Anitha M", "zone": "Shaft 1", "lat": 23.3428, "lng": 85.3080},
    "W004": {"name": "Kannan R", "zone": "Shaft 2", "lat": 23.3467, "lng": 85.3125},
    "W005": {"name": "Vijay S", "zone": "Loading Bay", "lat": 23.3439, "lng": 85.3140},
}

# ---------------------------------------------------
# Safety thresholds (editable by admin)
# ---------------------------------------------------
THRESHOLDS = {
    "methane_ppm_danger": 5000,      # methane gas danger level (ppm)
    "oxygen_percent_min": 19.5,      # minimum safe oxygen %
    "temperature_c_max": 45,         # max safe temperature
}


# ---------------------------------------------------
# Simulated live sensor reading for a worker
# (mini-project scope — replace with real IoT sensor feed later)
# ---------------------------------------------------
def get_worker_reading(worker_id):
    if worker_id not in WORKERS:
        return None

    w = WORKERS[worker_id]

    # simulate sensor values with some randomness
    methane = round(random.uniform(200, 6000), 1)
    oxygen = round(random.uniform(17.5, 21.0), 1)
    temperature = round(random.uniform(24, 48), 1)
    heart_rate = random.randint(60, 130)

    alerts = []
    status = "Safe"
    color = "green"

    if methane >= THRESHOLDS["methane_ppm_danger"]:
        alerts.append("High methane gas detected")
        status = "Danger"
        color = "red"
    if oxygen < THRESHOLDS["oxygen_percent_min"]:
        alerts.append("Low oxygen level")
        status = "Danger"
        color = "red"
    if temperature > THRESHOLDS["temperature_c_max"]:
        alerts.append("High temperature")
        if status != "Danger":
            status = "Warning"
            color = "yellow"
    if heart_rate > 120 or heart_rate < 55:
        alerts.append("Abnormal heart rate")
        if status == "Safe":
            status = "Warning"
            color = "yellow"

    return {
        "id": worker_id,
        "name": w["name"],
        "zone": w["zone"],
        "lat": w["lat"],
        "lng": w["lng"],
        "methane": methane,
        "oxygen": oxygen,
        "temperature": temperature,
        "heart_rate": heart_rate,
        "status": status,
        "color": color,
        "alerts": alerts,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
    }


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username in USERS and USERS[username] == password:
            session["user"] = username
            return redirect(url_for("index"))
        else:
            error = "Invalid username or password"
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


@app.route("/")
def index():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("index.html", user=session["user"])


@app.route("/map")
def map_view():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("map.html")


@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    if "user" not in session:
        return redirect(url_for("login"))
    if session["user"] not in ADMIN_USERS:
        return "Access denied — admin only.", 403

    message = None
    if request.method == "POST":
        try:
            THRESHOLDS["methane_ppm_danger"] = int(request.form.get("methane_ppm_danger"))
            THRESHOLDS["oxygen_percent_min"] = float(request.form.get("oxygen_percent_min"))
            THRESHOLDS["temperature_c_max"] = int(request.form.get("temperature_c_max"))
            message = "Thresholds updated successfully."
        except (ValueError, TypeError):
            message = "Invalid input — please enter numbers only."

    return render_template("admin.html", thresholds=THRESHOLDS, message=message, user=session["user"])


@app.route("/workers", methods=["GET"])
def workers_status():
    if "user" not in session:
        return jsonify({"error": "unauthorized"}), 401

    results = [get_worker_reading(wid) for wid in WORKERS]
    return jsonify(results)


@app.route("/sos", methods=["POST"])
def sos():
    if "user" not in session:
        return jsonify({"error": "unauthorized"}), 401
    worker_id = request.form.get("worker_id")
    if worker_id not in WORKERS:
        return jsonify({"error": "invalid worker"}), 400

    # In a real system this would trigger SMS/push notification to control room
    return jsonify({
        "message": f"SOS alert sent for {WORKERS[worker_id]['name']} ({worker_id})",
        "timestamp": datetime.now().strftime("%H:%M:%S"),
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
