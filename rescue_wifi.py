"""
Pi-Rescue

Automatic Wi-Fi recovery hotspot for headless Raspberry Pi.

Pi-Rescue is an automatic Wi-Fi recovery system for headless Raspberry Pi devices. 
When the Pi cannot connect to a saved Wi-Fi network, it starts a temporary recovery hotspot and provides a web portal for configuring a new connection.

Author: Hrithik
License: MIT
"""

import os
import sys
import json 
import time 
import subprocess

from flask import Flask, render_template, request, redirect, session

# config.json is the configuration fie,
# it stores portal settings and known Wi-Fi networks.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(BASE_DIR, "config.json")

app = Flask(__name__)
app.secret_key = "pi_rescue_secret"

portal_running = True

last_failure = ""
session_errors = {}   # Stores connection errors shown during the current login session only.

def load_config():

    with open(CONFIG, "r") as f:
        return json.load(f)


def save_config(cfg):

    with open(CONFIG, "w") as f:
        json.dump(cfg, f, indent=4)


def wifi_connected():   # Checks whether the Pi has a wifi connection.
    try:
        output = subprocess.check_output(["nmcli","-t","-f","GENERAL.CONNECTION", "device", "show", "wlan0"],text=True).strip()
        parts = output.split(":", 1)
        connection = parts[1].strip() if len(parts) > 1 else ""


        return connection not in ("--", "")

    except Exception:

        return False

def internet_available():
    try:
        subprocess.check_output(
            ["ping", "-c", "1", "8.8.8.8"],
            timeout=5,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except Exception:
        return False


def start_hotspot():

    subprocess.run(["nmcli", "connection", "up", "Pi-Rescue"])


def stop_hotspot():

    subprocess.run(["nmcli", "connection", "down", "Pi-Rescue"])


def scan_wifi():

    subprocess.run(["nmcli", "device", "wifi", "rescan"],stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    output = subprocess.check_output(["nmcli","-t","-f","SSID,SIGNAL,SECURITY","device","wifi","list","--rescan","yes"]).decode()

    nets = []

    cfg = load_config()
    hotspot_ssid = cfg["hotspot_ssid"]

# 
    seen = set()
    for line in output.splitlines():

        p = line.split(":")

# Remove duplicate SSIDs and hide the Pi-Rescue hotspot itself.
        if len(p) >= 3:

            ssid = p[0]
            if not ssid or ssid == hotspot_ssid or ssid in seen:
                continue

            seen.add(ssid)
            nets.append({
                "ssid": p[0],
                "signal": p[1],
                "security": p[2]
            })

    return nets


def connect_wifi(ssid, password):

# Stop the recovery hotspot before attempting a Wi-Fi connection.
    stop_hotspot()

    subprocess.run(["nmcli", "device", "disconnect", "wlan0"], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)

    time.sleep(3)
# Remove any existing NetworkManager profile to avoid reusing
# incorrect or outdated connection settings.

    subprocess.run(["nmcli", "connection", "delete", ssid],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

    result = subprocess.run(["nmcli","device","wifi","connect",ssid,"password",password],capture_output=True,text=True)

    time.sleep(10)

    if result.returncode != 0:
        return False, result.stderr.strip()

    ip_output = subprocess.check_output(["nmcli", "-t", "-f", "IP4.ADDRESS", "device", "show", "wlan0"]).decode().strip()

    if not ip_output:

        return False, "DHCP timeout"

    if internet_available():

        return True, "Connected"

    time.sleep(8)

    
    return True, "Connected to Wi-Fi but no Internet"

def check_internet():
    try:
        subprocess.check_output(["ping", "-c", "3", "8.8.8.8"],timeout=5)

        return True
    except:
        return False

def save_wifi(ssid, password):

    cfg = load_config()
    entry = cfg["known_networks"].get(ssid)

    if entry is None:

        cfg["known_networks"][ssid] = {
            "password": password,
            "priority": 50,
            "status": "Saved",
            "last_connected": "",
            "last_error": "",
            "logs": []
        }
    else:
        if isinstance(entry,str):

            entry={
              "password":entry,
              "priority":50,
              "status":"Saved",
              "last_connected":"",
              "last_error":"",
              "logs":[]
           }

        entry["password"] = password
        cfg["known_networks"][ssid] = entry

    save_config(cfg)



@app.route("/")
def index():

    if session.get("logged"):
        return redirect("/wifi")

    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():

    cfg = load_config()

    if request.form["password"] == cfg["portal_password"]:

        session["logged"] = True

        session_errors.clear()
        return redirect("/wifi")

    return redirect("/")


@app.route("/wifi")
def wifi():

    if not session.get("logged"):
        return redirect("/")

    cfg = load_config()

    networks = scan_wifi()

    for n in networks:

        n["error"] = session_errors.get(n["ssid"],"")

        n["saved"] = n["ssid"] in cfg["known_networks"]

    return render_template(
        "wifi.html",
        networks=networks,
        failure=""
    )

@app.route("/ping")
def ping():

    return"pong"

@app.route("/refresh")
def refresh():

    if not session.get("logged"):
        return redirect("/")

    return redirect("/wifi")

@app.route("/exit")
def exit_portal():

    session.clear()

    return redirect("/")

@app.route("/terminate")
def terminate():

    time.sleep(1)

    stop_hotspot()

    os._exit(0)

@app.route("/password", methods=["POST"])
def password():

    if not session.get("logged"):
        return redirect("/")

    ssid = request.form["ssid"]

    cfg = load_config()

    #Prevent the users from atttempting to connect to the Pi-Rescue hotspot itself.

    if ssid == cfg["hotspot_ssid"]:
        return redirect("/wifi")

    entry = cfg["known_networks"].get(ssid)

    if entry is not None:
        saved_password = entry if isinstance(entry, str) else entry.get("password", "").strip()
        if saved_password:
            return attempt_connection(ssid, saved_password)
 


    return render_template("password.html", ssid=ssid)

def attempt_connection(ssid, password):
    global last_failure
    cfg = load_config()
    ensure_entry(cfg, ssid)  # Ensure whether an entry exists for a network defore  updating its status.

    save_config(cfg)

    success, message = connect_wifi(ssid, password)

    cfg = load_config()
    entry = ensure_entry(cfg, ssid)
    if not success:


        cfg = load_config()

        if "Secrets were required" in message:    # Clear the saved password only if authentication failed to prevent repeated connection attempts using an incorrect passsword.

            display_error = "Wrong Password" 
            clear_password = True

        elif "DHCP timeout" in message:
            display_error = "DHCP timeout"
            clear_password = False
        else:
            display_error = message
            clear_password = False

        if clear_password:
            entry["password"] = ""

        entry["status"] = "Failed"
        entry["last_error"] = display_error
        add_log(cfg, ssid, display_error)
        save_config(cfg)

        session_errors[ssid] = display_error
        start_hotspot()
        time.sleep(2)

        return redirect("/wifi")

    save_wifi(ssid, password)

    cfg = load_config()
    entry = ensure_entry(cfg, ssid)
    entry["status"] = "Connected"
    entry["last_connected"] = time.strftime("%Y-%m-%d %H:%M:%S")
    entry["last_error"] = ""

    add_log(cfg, ssid, message)
    save_config(cfg)

    session_errors.pop(ssid, None)

    return "Pi-Rescue Terminated"


@app.route("/connect", methods=["POST"])
def connect():

    if not session.get("logged"):
        return redirect("/")

    ssid = request.form["ssid"]
    password = request.form["password"]

    return attempt_connection(ssid, password)

def add_log(cfg, ssid, result):

    entry = cfg["known_networks"][ssid]
    logs = entry.get("logs",[])

    if not isinstance(logs, list):
        logs = []

    logs.insert(0,{
      "time":time.strftime("%Y-%m-%d %H:%M:%S"),
      "result":result
    })

    entry["logs"] = logs[:15]

def ensure_entry(cfg, ssid):

# Upgrade older configuration formats that stored only the password
# into the newer dictionary-based structure.
    entry = cfg["known_networks"].get(ssid)
    if entry is None:
        cfg["known_networks"][ssid] = {
            "password":"",
            "priority":50,
            "status":"New",
            "last_connected":"",
            "last_error":"",
            "logs":[],
        }
    elif isinstance(entry, str):
        cfg["known_networks"][ssid]={
            "password":entry,
            "priority":50,
            "status":"Saved",
            "last_connected":"",
            "last_error":"",
            "logs":[],
        }
    return cfg["known_networks"][ssid]

def rescue_mode():

# Start the recovery hotspot and launch the Flask portal.
    start_hotspot()
    time.sleep(2)


    app.run(
        host="0.0.0.0",
        port=80,
        debug=False
    )


if __name__ == "__main__":

    # Gives NetworkManager a few seconds to establish a normal Wi-Fi connection after boot.
    time.sleep(15)

    # If Wi-Fi is already connected,recovery mode is not required.
    if wifi_connected():
        
        sys.exit(0)
    else:
        rescue_mode()
