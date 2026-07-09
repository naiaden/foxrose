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
  main_server: "192.168.88.23"
  frigate_server: "192.168.88.22"

# Door stations
doors:
  achterdeur:
    ip: "192.168.88.200"
    account: "admin"
    password: "w4chtwoord"

# Users configuration
users:
  - name: louis
    telegram_id: 11799898
    keycards:
      - 22337d12
      - b4130231
  - name: ruth
    telegram_id: 164900585
    keycards:
      - 84f6f930

# Valid doorcard IDs (for access control)
valid_doorcards:
  - b4130231
  - 14a1f930

# Frigate cameras
frigate_cameras:
  - achterdeur
  - tuinhuis
  - voordeur

# Temperature sensors
thermometers:
  "0xa4c13805db71defe": Rosa
  "0xa4c13849284553bd": Finn
```

### .env (Secrets only)

Only secrets are stored in `.env`:

| Variable | Description |
|----------|-------------|
| `BOT_TOKEN` | Telegram bot token (required) |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, etc.) |
| `LOG_FILE` | Log file path |
| `CONFIG_PATH` | Custom config file path (optional) |

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

3. **Snooze**:
   - 💤 Snooze Notifications - Temporarily disable notifications
   - ⏳ 15 Mins, 1 Hour, 3 Hours, 8 Hours - Snooze duration options
   - ⏰ Unsnooze - Cancel snooze early

### MQTT Topics

The system subscribes to:

**Main MQTT Broker:**
- `DahuaVTO/DoorCard/Event/#` - Door access events
- `DahuaVTO/Invite/Event/#` - Doorbell invites
- `zigbee2mqtt/+` - Zigbee sensor data (battery, temperature, presence)
- `foxrosehip/bot/users/+/cameras/+` - User camera preference updates
- `foxrosehip/afval` - Waste collection notifications

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
├── main.py              # Application entry point
├── state.py             # State manager (users, sensors, modes)
├── users.py             # User and UserManager classes
├── sensors.py           # Sensor and SensorSystem classes
├── modes.py             # Mode enum (AT_HOME, AWAY, NIGHT, STANDARD)
├── temperatures.py      # Temperature tracking and trends
├── logging_config.py    # Loguru configuration
├── config.py            # YAML configuration loader
├── api.py               # Legacy API entry point
│
├── events/              # Event definitions
│   ├── event.py         # Base Event class
│   ├── afval_event.py   # Waste collection events
│   ├── change_event.py  # User settings change events
│   ├── detection_event.py # Camera/presence detection events
│   ├── device_event.py  # Battery/temperature device events
│   └── doorcard_event.py # Door access events
│
├── handlers/            # Event handlers
│   ├── mqtt.py          # MQTT dispatchers
│   └── telegram.py      # Telegram bot handler
│
├── routing/             # Event routing
│   ├── router.py        # NotificationRouter
│   ├── rules.py         # Mode-based delivery rules
│   └── event_handlers/  # Individual event handler classes
│       ├── __init__.py
│       ├── afval.py
│       ├── user_settings.py
│       ├── snooze.py
│       ├── mode_toggle.py
│       ├── doorcard.py
│       ├── camera_detection.py
│       ├── device.py
│       ├── temperature.py
│       └── presence.py
│
├── sinks/               # Notification delivery
│   ├── base.py          # Abstract NotificationSink
│   ├── telegram.py      # Telegram message delivery
│   └── console.py       # Console logging sink
│
└── systems/             # System integrations
    ├── notification.py  # Notification system
    ├── camera.py        # Camera system
    └── dahua.py         # Dahua door station integration
```

## License

MIT License