# FoxRose Smart

A REST/HTTP API for controlling Philips Hue lights across multiple bridges, exposing room-level, lamp-level, and home-wide operations.

## Goal

This service provides a programmable interface for home lighting control:

- **Multi-bridge support**: Manage multiple Hue bridges in a single API surface
- **Room operations**: Toggle, nightlight, and scene rotation on a per-room basis
- **Lamp control**: Individual lamp state, brightness, and colour management
- **Home overview**: Aggregate state reporting (`home_active`, `nr_bridges`)
- **Scene management**: Rotate through scenes, activate orientation / bright / nightlight presets

## Setup

### Prerequisites

- Python 3.12+
- One or more Philips Hue bridges on your network
- Hue API keys (obtained via the Hue bridge pairing process)

### Quick Start (Local)

1. **Create environment file**
   ```bash
   cp .env.example .env
   ```

2. **Configure your environment** — edit `.env` and fill in your real values:
      ```env
   # Hue bridge IPs (replace with your actual bridge addresses)
   HUE_IP=192.168.1.100
   HUE1_IP=192.168.1.101

   # Hue API keys (obtained via the Hue bridge pairing process)
   HUE_KEY=your-first-bridge-key
   HUE1_KEY=your-second-bridge-key
   ```

3. **Create config file**
   ```bash
   cp config.example.yaml config.yaml
   ```

4. **Install dependencies and run**
   ```bash
   pip install -r requirements.txt
   uvicorn src.api:app --env-file .env --host 0.0.0.0 --port 8555
   ```

5. **Open the interactive docs**: http://localhost:8555/docs

### Quick Start (Docker)

```bash
cp .env.example .env
# → edit .env with your real Hue keys
cp config.example.yaml config.yaml
docker compose up -d --build
```

The API will be available at http://localhost:8555 and the auto-generated docs at http://localhost:8555/docs.

### Quick Start (FastAPI CLI)

```bash
cp .env.example .env
cp config.example.yaml config.yaml
pip install -r requirements.txt
fastapi dev src/api.py
```

> **Note**: `fastapi dev` does **not** automatically load `.env` files. If `GET /home` reports `nr_bridges=0`, use `uvicorn src.api:app --env-file .env` instead.

## Configuration

Configuration is split across two files:

### `.env` (Sensitive — do not commit)

| Variable | Required | Default | Description |
|---|---|---|---|
| `HUE_IP` | Yes | — | IP address of the first Hue bridge |
| `HUE1_IP` | Yes | — | IP address of the second Hue bridge |
| `HUE_KEY` | Yes | — | API key for the first bridge |
| `HUE1_KEY` | Yes | — | API key for the second bridge |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity |
| `LOG_FILE` | No | — | Optional path for log output (e.g. `/var/log/foxrose/app.log`) |

### `config.yaml` (Non-sensitive)

```yaml
# Default rooms to activate when toggling home on (optional)
default_active_rooms:
  - eetkamer
  - woonkamer
```

## API Reference

All endpoints respond under the root path (no global prefix).

### Home

| Method | Path | Description |
|---|---|---|
| `GET` | `/home` | Overview of home state (`home_active`, `nr_bridges`) |
| `POST` | `/home/update` | Re-sync with bridges (new scenes, lights, rooms) |
| `POST` | `/home/active/toggle` | Turn all lights off if any are on; otherwise activate default rooms |
| `POST` | `/home/active/{active}` | Set all rooms to `on` or `off` |

### Rooms

`{room_id}` path parameters render a **dropdown** in the Swagger UI, populated from your discovered rooms.

| Method | Path | Description |
|---|---|---|
| `GET` | `/room` | List all rooms as `[[name, id], ...]` |
| `GET` | `/room/{room_id}` | Summary of a room (lamp count, scene count, group count) |
| `GET` | `/room/{room_id}/scenes` | List of scene names available in the room |
| `POST` | `/room/{room_id}/active/{active}` | Turn all lamps in the room `on` or `off` |
| `POST` | `/room/{room_id}/night` | Activate the "Nightlight" scene (if defined) |
| `POST` | `/room/{room_id}/scene/next` | Rotate to the next scene (stateful — remembers position per room) |
| `POST` | `/room/{room_id}/scene/orientation` | Activate the "orientatie" scene (if defined) |
| `POST` | `/room/{room_id}/scene/bright` | Activate the "Bright" scene (if defined) |

### Lamps

| Method | Path | Description |
|---|---|---|
| `GET` | `/lamp/{lamp_id}` | Summary of a lamp (name, id, on/off, brightness, colour) |
| `POST` | `/lamp/{lamp_id}/active/{active}` | Turn lamp `on` or `off` |
| `POST` | `/lamp/{lamp_id}/brightness/{step}` | Adjust brightness by `step` (clamped to 0–100) |
| `POST` | `/lamp/{lamp_id}/colour/{colour_value}` | Set colour (CT mired value) |

### Root

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Health check — returns `{"message": "Hello World"}` |

## Development

### Testing

```bash
pip install pytest pytest-cov
pytest tests/ -v
```

Tests use mocked `Home` objects — no real Hue bridges are required:

```bash
pytest tests/ -v --cov=src
```

### Linting

```bash
ruff check src/ tests/
black src/ tests/
```

Pre-commit hooks are configured via `.pre-commit-config.yaml`:

```bash
pre-commit install
pre-commit run --all-files
```

## License

MIT License
