# Pi-Rescue v1.0

## Automatic Wi-Fi Recovery Hotspot for Headless Raspberry Pi

Pi-Rescue is a recovery system for headless Raspberry Pi devices that
automatically creates a temporary Wi-Fi hotspot whenever the Pi cannot
reconnect to a known wireless network.

Instead of losing SSH access and having to connect a monitor, keyboard,
or serial console, Pi-Rescue provides a web-based recovery portal that
allows you to reconnect the Raspberry Pi to a Wi-Fi network directly
from your phone or computer.

The project is designed around NetworkManager and is intended for modern
Raspberry Pi OS installations.

## Why Pi-Rescue?

Headless Raspberry Pis are often installed in locations where connecting
a monitor or keyboard is inconvenient---or impossible.

Losing network connectivity can happen for many reasons:

-   Wi-Fi password changed
-   Router replaced
-   Access point unavailable
-   Incorrect credentials
-   Filesystem corruption after an unexpected shutdown
-   Network configuration problems

When this happens, SSH becomes unavailable and the Raspberry Pi will not
be accessible at that situation.

Pi-Rescue solves this by automatically starting a recovery hotspot
whenever the Pi cannot reconnect to a saved Wi-Fi network.

## Features

-   Automatic recovery hotspot
-   Headless Wi-Fi recovery
-   Login-protected web portal
-   Scan nearby Wi-Fi networks
-   Connect to new Wi-Fi networks
-   Save known Wi-Fi credentials
-   Network priority management
-   Connection status logging
-   Failure tracking
-   Internet connectivity verification
-   Clean hotspot shutdown after successful connection
-   Built using Flask and NetworkManager

## Pi-Rescue Workflow

``` text
Pi Boots
   |
   v
systemd starts Pi-Rescue
   |
   v
rescue_wifi.py starts
   |
   v
Attempt to connect with saved Wi-Fi
   |
   +-------------------+
   |                   |
Connected             Failed
   |                   |
   v                   v
Normal Operation    Start Pi-Rescue
                    Hotspot
                       |
                       v
                Connect Phone/Laptop
                       |
                       v
                Recovery Web Portal
                       |
                       v
             Select Wi-Fi & Enter Password
                       |
                       v
              NetworkManager attempts
                    Connection
                       |
               +-------+-------+
               |               |
             Success         Failure
               |               |
               v               v
         Stop Hotspot      Return to Portal
               |           & Display Error
               v
        Normal Operation
```

## Workflow

### 1. Pi Boots

Pi boots and systemd starts the Pi-Rescue service.

### 2. Saved Wi-Fi Connection

Pi-Rescue attempts to connect to a saved Wi-Fi network.

### 3. Connection Check

-   **Connected:** Continue normal operation.
-   **Failed:** Start the Pi-Rescue hotspot.

### 4. Recovery

-   Connect a phone or laptop to the Pi-Rescue hotspot.
-   Open the Recovery Web Portal.
-   Select a Wi-Fi network and enter its password.

### 5. Connection Attempt

Pi-Rescue uses NetworkManager to attempt the Wi-Fi connection.

### 6. Result

-   **Success:** Stop the hotspot and resume normal operation.
-   **Failure:** Return to the portal and display the connection error.

## How It Detects Failure

Pi-Rescue waits for the configured timeout period after boot for NetworkManager to establish a Wi-Fi connection.

The program checks the status of `GENERAL.CONNECTION`. If no valid connection is detected within the configured timeout period, 
Pi-Rescue enters rescue mode and starts the hotspot.

## Recovery Portal

The recovery portal is designed to be simple and easy to use.

It provides:

-   Login authentication
-   Nearby Wi-Fi scanning
-   Saved network support
-   Password entry
-   Connection status
-   Error reporting
-   Recovery termination after successful setup

The entire recovery process can be completed from a mobile phone or any
Wi-Fi-enabled device.

## Accessing the Portal

After connecting to the Pi-Rescue hotspot, open a browser and go to:

``` text
http://10.42.0.1
```

If the page does not load:

-   Ensure you are connected to the Pi-Rescue Wi-Fi network.
-   Disable mobile data on phones.
-   Try `http://10.42.0.1:80` if using the Flask default port.

## Project Structure

``` text
Pi-Rescue/
├── rescue_wifi.py          # Main application
├── config.example.json     # Example configuration
├── requirements.txt
├── pi-rescue.service
├── README.md
├── LICENSE
├── .gitignore
├── templates/
│   ├── login.html
│   └── wifi.html
├── static/
├── screenshots/
└── docs/
```

## Requirements

### Hardware

-   Raspberry Pi Zero 2 W
-   Raspberry Pi 3
-   Raspberry Pi 4
-   Raspberry Pi 5

### Software

-   Raspberry Pi OS (Bookworm or newer)
-   Python 3
-   NetworkManager
-   Flask

## Installation

### Clone the repository

``` bash
git clone https://github.com/Kernovax/Pi-Rescue.git
```

### Move into the project directory

``` bash
cd Pi-Rescue
```
### Configure the Wi-Fi Connection Timeout

By default, Pi-Rescue waits **15 seconds** after boot for NetworkManager to establish a Wi-Fi connection before starting the recovery hotspot.

The timeout can be changed according to your network setup or requirements.

In `rescue_wifi.py` file, locate:

```python
time.sleep(15)
```

Change `15` to the desired number of seconds.

### Install dependencies

``` bash
pip install -r requirements.txt
```

### Create Your Configuration

Run the following command to create your configuration file (config.json):

``` bash
cp config.example.json config.json
```
This command creates `config.json` and copies the contents of `config.example.json` into it.

Open the newly created configuration file:

```bash
nano config.json
```

**Important:** The `config.example.json` included in this repository is only an example configuration. Before running Pi-Rescue, edit `config.json` and replace the placeholder values with your actual hotspot name, password, and other settings. Do not commit a modified `config.json` containing your real passwords or Wi-Fi credentials to the public repository.

### Test Pi-Rescue manually

``` bash
python3 rescue_wifi.py
```

## Startup Service

Pi-Rescue can be configured as a systemd service so that it starts automatically when the Raspberry Pi boots.

### 1. Service File

The systemd service configuration is provided in `Pi-Rescue.service`.

Before installing the service file, open the service file from the repository:

```bash
nano Pi-Rescue.service
```

Update the `User` and `ExecStart` values in the
service file to match your system.

### 2. Copy the Service File

``` bash
sudo cp Pi-Rescue.service /etc/systemd/system/
```

### 3. Reload systemd

``` bash
sudo systemctl daemon-reload
```

### 4. Enable Pi-Rescue at Startup

``` bash
sudo systemctl enable Pi-Rescue.service
```

This makes Pi-Rescue start automatically whenever the Raspberry Pi
boots.

### 5. Start the Service

``` bash
sudo systemctl start Pi-Rescue.service
```

### 6. Check the Service Status

``` bash
sudo systemctl status Pi-Rescue.service
```

If everything is working correctly, the service should show:

``` text
Active: active (running)
```

### 7. View Pi-Rescue Logs

To view the service logs:

``` bash
journalctl -u Pi-Rescue.service
```

## config.json Overview

Pi-Rescue uses `config.json` file to store its configurations and Wi-Fi information:

-   Web page login password
-   Hotspot SSID
-   Hotspot password
-   Wi-Fi passwords 
-   Wi-Fi connection status
-   Last 15 logs of Wi-Fi connections


## Use Cases

Pi-Rescue is useful for:

-   Remote Raspberry Pi installations
-   IoT devices
-   Robots
-   Home automation
-   Raspberry Pi servers
-   Classroom Raspberry Pis
-   Embedded Linux projects
-   Any headless Raspberry Pi deployment

## Current Status

**Working Prototype of v1.0**

Pi-Rescue is currently designed primarily for Raspberry Pi setups that rely on Wi-Fi for network access, so Ethernet detection is not included in v1.0 of Pi-Rescue.

Current features include:

-   Automatic hotspot fallback
-   Recovery web portal
-   Login protection
-   Wi-Fi scanning
-   Network connection management
-   Connection logging
-   Internet verification

Additional improvements and new features are planned.

## Current Limitation

The current version checks the Wi-Fi interface (wlan0) when deciding whether recovery mode is required. If the Raspberry Pi has an active Ethernet connection, Pi-Rescue may still start the recovery hotspot even though the Pi is already reachable through Ethernet.

Ethernet connection detection and overall network-state detection are planned for a future revision.

## Roadmap

Planned ideas include:

-   QR code for hotspot connection (with OLED display)
-   Improved mobile interface
-   HTTPS support
-   Better diagnostics
-   Plugin architecture for modular extensions
-   OTA update support for remote software updates

## Contributing

Contributions, bug reports, feature requests, and suggestions are
welcome.

If you discover an issue or have an idea for improvement, please open an
Issue or submit a Pull Request.

## Troubleshooting

### Hotspot starts but web page does not load

Check if Flask is running:

``` bash
sudo ss -tlnp | grep 5000
```

Ensure the application is bound to:

``` python
app.run(host="0.0.0.0")
```

### Cannot access 10.42.0.1

-   Make sure your device is connected to Pi-Rescue Wi-Fi.
-   Disable mobile data.
-   Restart the Wi-Fi connection.

### Rescue mode does not start

Check logs:

``` bash
journalctl -u your-service-name
```

Run manually:

``` bash
python3 rescue_wifi.py
```

### Connected to Pi-Rescue Wi-Fi but web page not available

Check whether the Pi-Rescue service's autoconnect priority is disabled.

## License

This project is released under the MIT License.

## Acknowledgements

Pi-Rescue was developed to simplify Wi-Fi recovery for headless
Raspberry Pi systems and reduce the need for physical access after
network failures.
