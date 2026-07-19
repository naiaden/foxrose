# FoxRose Event Handler

A home automation event handling system that processes MQTT events from security cameras, door access systems, sensors, and other smart home devices, routing notifications to users via Telegram based on configurable modes and preferences.

## Goal

This system provides intelligent notification routing for home security and automation:

- **Camera Detection**: Receives motion/person detection events from Frigate NVR and sends snapshot notifications
- **Door Access**: Handles doorcard (RFID key fob) events for access control
- **Presence Detection**: Processes indoor/outdoor presence sensor events
- **Temperature Monitoring**: Tracks temperature trends from sensors
- **Battery Monitoring**: Alerts on low battery devices
- **Afval (Waste) Collection**: Sends waste collection reminders
- **System Monitoring**: Monitors host system resources (CPU, swap, disk) and alerts on threshold breaches

The system supports multiple user modes (At Home, Away, Night, Standard) to control notification behavior based on context.

## Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   MQTT Topics   │────▶│  Event Handlers  │────▶│ Notification    │
│ (Frigate,       │      │  (router.py)     │      │  Router         │
│  Zigbee, etc.)  │      └──────────────────┘      └────────┬────────┘
└─────────────────┘                                         │
                                                            ▼
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   Telegram      │◀────│   Sinks          │◀────│  State Manager  │
│   Bot           │      │ (telegram,       │      │  (users, modes, │
│                 │      │  console)        │      │   sensors)      │
└─────────────────┘      └──────────────────┘      └─────────────────┘
```

### Key Components

- **Event System** (`src/events/`): Dataclass-based events with colorized logging
- **Handlers** (`src/handlers/`): MQTT dispatchers and Telegram bot commands
- **Router** (`src/routing/`): Event routing with mode-based delivery rules
- **Sinks** (`src/sinks/`): Notification delivery (Telegram, Console)
- **State** (`src/state.py`): User management, mode tracking, sensor state
- **System Monitor** (`system_monitor.py`): Standalone daemon that monitors host resources and publishes to MQTT

## Setup

### Prerequisites

- Python 3.12+
- MQTT broker (e.g., Mosquitto)
- Frigate NVR for camera events
- Zigbee2MQTT for sensor events
- Dahua VTO door station for doorcard events

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/naiaden/foxrose.git
   cd foxrose/event
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   ```

3. **Configure environment variables** (see Configuration section below)

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Docker Installation

```bash
docker-compose up -d
```

## Configuration

The system uses a two-file configuration approach:

### config.yaml (Non-sensitive configuration)

All non-sensitive configuration is stored in `config.yaml`:

```yaml
# MQTT Configuration
mqtt:
  main_server: "192.168.1.100"
  frigate_server: "192.168.1.101"

# Door stations
doors:
  back_door:
    ip: "192.168.1.10"
    account: "admin"
    password: "your_password"

# Users configuration
users:
  - name: alice
    telegram_id: 123456789
    keycards:
      - card_id_1
      - card_id_2
  - name: bob
    telegram_id: 987654321
    keycards:
      - card_id_3

# Valid doorcard IDs (for access control)
valid_doorcards:
  - card_id_1
  - card_id_2

# Frigate cameras
frigate_cameras:
  - back_door
  - patio
  - front_door

# Temperature sensors
thermometers:
  "0x_sensor_id_1": "Living Room"
  "0x_sensor_id_2": "Bedroom"

# System monitoring configuration
system_monitor:
  cpu_threshold: 80.0      # CPU usage alert threshold (%)
  swap_threshold: 90.0     # Swap usage alert threshold (%)
  tmp_threshold: 90.0      # /tmp disk usage alert threshold (%)
  check_interval: 60       # Check interval in seconds
```

### .env (Secrets only)

Only secrets are stored in `.env`:

| Variable | Description |
|----------|-------------|
| `BOT_TOKEN` | Telegram bot token (required) |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, etc.) |
| `LOG_FILE` | Log file path |
| `CONFIG_PATH` | Custom config file path (optional) |
| `SYSTEM_MONITOR_CPU_THRESHOLD` | CPU usage threshold (default: 80.0) |
| `SYSTEM_MONITOR_SWAP_THRESHOLD` | Swap usage threshold (default: 90.0) |
| `SYSTEM_MONITOR_TMP_THRESHOLD` | /tmp usage threshold (default: 90.0) |
| `SYSTEM_MONITOR_CHECK_INTERVAL` | Check interval in seconds (default: 60) |
| `SYSTEM_MONITOR_MQTT_SERVER` | MQTT broker address (default: localhost) |

### Creating Configuration

1. Copy the example config:
   ```bash
   cp config.yaml config.local.yaml
   ```

2. Edit `config.local.yaml` with your settings

3. Create `.env` with your secrets:
   ```bash
   cp .env.example .env
   # Edit .env to add BOT_TOKEN
   ```

4. Run with custom config (optional):
   ```bash
   CONFIG_PATH=config.local.yaml python src/main.py
   ```

## Usage

### Running the Application

```bash
python src/main.py
```

Or with Docker:
```bash
docker-compose up -d
```

### Running the System Monitor

The system monitor is a separate daemon that monitors host resources and publishes alerts to MQTT:

```bash
python system_monitor.py
```

Or with custom settings:
```bash
python system_monitor.py --cpu-threshold 85 --swap-threshold 95 --check-interval 30
```

Or via environment variables:
```bash
SYSTEM_MONITOR_CPU_THRESHOLD=85 SYSTEM_MONITOR_MQTT_SERVER=192.168.1.100 python system_monitor.py
```

**Systemd Service Example:**

Create `/etc/systemd/system/foxrose-monitor.service`:
```ini
[Unit]
Description=FoxRose System Monitor
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/foxrose/event
ExecStart=/usr/bin/python3 system_monitor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable --now foxrose-monitor.service
```

### Telegram Bot Commands

Users can interact with the bot via Telegram:

| Command | Description |
|---------|-------------|
| `/start` | Initialize the bot and show control keyboard |
| `/state` | Display current system status (mode, cameras, temperatures, presence) |

### Interactive Controls

The bot provides a persistent keyboard with:

1. **Mode Selection**:
   - 🌐 All - Standard mode (all notifications)
   - 🧳 Away - Away mode (all events trigger)
   - 🌙 Night - Night mode (silent indoor, loud outdoor)
   - 🏠 At Home - Home mode (silent camera, ignore indoor presence)

2. **Camera Notification Toggles**:
   - 🔔/🔕 Notif: `<camera>` - Toggle notifications per camera

3. **Snapshots**:
   - 📸 All Snapshots - Fetch and send snapshots from all cameras
   - 📷 Select Camera - Choose a specific camera for snapshot

4. **Snooze**:
   - 💤 Snooze All - Temporarily disable all notifications
   - ⏳ 15 Mins, 1 Hour, 3 Hours, 8 Hours - Snooze duration options
   - ⏰ Unsnooze - Cancel snooze early
   - 🎯 Snooze Specific - Toggle snooze for specific event types:
     - Indoor Presence
     - Outdoor Presence
     - Camera Detection

### MQTT Topics

The system subscribes to:

**Main MQTT Broker:**
- `DahuaVTO/DoorCard/Event/#` - Door access events
- `DahuaVTO/Invite/Event/#` - Doorbell invites
- `zigbee2mqtt/+` - Zigbee sensor data (battery, temperature, presence)
- `foxrosehip/bot/users/+/cameras/+` - User camera preference updates
- `foxrosehip/afval` - Waste collection notifications
- `foxrosehip/system/{hostname}/cpu` - High CPU usage alerts
- `foxrosehip/system/{hostname}/swap` - High swap usage alerts
- `foxrosehip/system/{hostname}/tmp` - High /tmp disk usage alerts

**Frigate MQTT:**
- `frigate/+/+/snapshot` - Camera snapshots
- `frigate/events` - Frigate event stream

## Development

### Running Tests

```bash
pytest
```

### Project Structure

```
src/
├── main.py                 # Application entry point
├── state.py                # State manager (users, sensors, modes)
├── users.py                # User and UserManager classes
├── sensors.py              # Sensor and SensorSystem classes
├── modes.py                # Mode enum (AT_HOME, AWAY, NIGHT, STANDARD)
├── temperatures.py         # Temperature tracking and trends
├── logging_config.py       # Loguru configuration
├── config.py               # YAML configuration loader
├── api.py                  # Legacy API entry point
│
├── events/                 # Event definitions
│   ├── __init__.py
│   ├── event.py            # Base Event class
│   ├── afval_event.py      # Waste collection events
│   ├── change_event.py     # User settings change events
│   ├── detection_event.py  # Camera/presence detection events
│   ├── device_event.py     # Battery/temperature device events
│   ├── doorcard_event.py   # Door access events
│   └── system_event.py     # System monitoring events (CPU, swap, disk)
│
├── handlers/               # Event handlers
│   ├── mqtt.py             # MQTT dispatchers
│   └── telegram.py         # Telegram bot handler
│
├── routing/                # Event routing
│   ├── router.py           # NotificationRouter
│   ├── rules.py            # Mode-based delivery rules
│   └── event_handlers/     # Individual event handler classes
│       ├── __init__.py
│       ├── afval.py
│       ├── user_settings.py
│       ├── snooze.py
│       ├── mode_toggle.py
│       ├── doorcard.py
│       ├── camera_detection.py
│       ├── device.py
│       ├── temperature.py
│       ├── presence.py
│       └── system.py       # System event handler
│
├── sinks/                  # Notification delivery
│   ├── base.py             # Abstract NotificationSink
│   ├── telegram.py         # Telegram message delivery
│   └── console.py          # Console logging sink
│
└── systems/                # System integrations
    ├── notification.py     # Notification system
    ├── camera.py           # Camera system
    └── dahua.py            # Dahua door station integration

system_monitor.py           # Standalone system resource monitoring daemon
```

## Snooze Functionality

The snooze feature allows users to temporarily disable notifications:

### Snooze All Notifications

- Tap **💤 Snooze All** to snooze all notifications
- Select a duration: **⏳ 15 Mins**, **⏳ 1 Hour**, **⏳ 3 Hours**, or **⏳ 8 Hours**
- Tap **⏰ Unsnooze** to cancel snooze early
- During snooze, all notifications are suppressed except critical system alerts

### Snooze Specific Event Types

- Tap **🎯 Snooze Specific** to toggle snooze for individual event types:
  - Indoor Presence
  - Outdoor Presence
  - Camera Detection
- Each type can be toggled independently (🔔/🔕)
- This allows fine-grained control over which notifications to receive

## Snapshots

The snapshot feature allows users to request camera snapshots on demand:

### All Snapshots

- Tap **📸 All Snapshots** to fetch and send snapshots from all configured cameras
- Snapshots are retrieved from the Frigate NVR
- Images are sent directly to the Telegram chat

### Select Camera

- Tap **📷 Select Camera** to choose a specific camera
- A keyboard with all available cameras will appear
- Tap a camera button (e.g., **📸 Snap: Achterdeur**) to get a snapshot
- The snapshot is fetched from Frigate and sent to the chat

## System Monitoring

The system monitor (`system_monitor.py`) is a standalone daemon that:

- Monitors CPU, swap, and /tmp disk usage
- Publishes alerts to MQTT when thresholds are exceeded
- Includes hostname in MQTT topics for multi-host deployments
- Configurable thresholds and check intervals

### MQTT Payload Format

```json
{
  "hostname": "foxrose-server",
  "cpu_percentage": 85.5,
  "threshold": 80.0
}
```

### Event Types

- **HighCPUEvent**: CPU usage exceeded threshold
- **HighSwapUsageEvent**: Swap usage exceeded threshold
- **HighTmpUsageEvent**: /tmp disk usage exceeded threshold

All system events include the hostname for identification in multi-host environments.

## License

MIT License