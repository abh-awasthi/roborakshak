# RoboRakshak Installation and Run Guide

This guide documents the project as it currently behaves.

## Canonical Install Flow (Raspberry Pi)

```bash
git clone https://github.com/abh-awasthi/roborakshak.git
cd roborakshak
sudo bash install.sh
```

The installer currently does the following:
- updates apt packages
- creates a Python virtual environment
- installs dependencies from `requirements.txt`
- writes `/etc/systemd/system/roborakshak.service`
- enables and starts `roborakshak.service`
- creates `INSTALLATION_COMMANDS.md`

## Local Development (Mock Run)

Use mock GPIO when you are developing on a laptop or a machine without Raspberry Pi hardware.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
FORCE_MOCK=1 python3 backend/app.py
```

The app will run in mock mode and log GPIO actions instead of driving motors.

Open `http://localhost:5000`.

## Raspberry Pi / Actual Run

On the Pi, install dependencies and run without forcing mock mode:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 backend/app.py
```

**Driver login is required before motor controls work.**
- Default driver PIN: `4321`
- Viewer PIN: `1111`

Or use the installer for automatic service setup:

```bash
sudo bash install.sh
```

Do not set `FORCE_MOCK` on the actual robot unless you specifically want a dry-run.

## FORCE_MOCK Behavior

`backend/app.py` attempts to import `RPi.GPIO`. If import fails, it falls back to mock GPIO automatically.

You can force mock mode explicitly:

```bash
FORCE_MOCK=1 python3 backend/app.py
```

You can also export it for your shell session:

```bash
export FORCE_MOCK=1
python3 backend/app.py
```

For systemd runtime override:

```bash
sudo systemctl set-environment FORCE_MOCK=1
sudo systemctl restart roborakshak.service
```

To return to normal mode:

```bash
sudo systemctl unset-environment FORCE_MOCK
sudo systemctl restart roborakshak.service
```

## API Endpoints (Current)

- `POST /api/motor/forward`
- `POST /api/motor/backward`
- `POST /api/motor/left`
- `POST /api/motor/right`
- `POST /api/motor/rotate/left`
- `POST /api/motor/rotate/right`
- `POST /api/motor/stop`
- `POST /api/motor/speed/<int:speed>`
- `GET /api/status`

## Service Operations

```bash
sudo systemctl status roborakshak.service
sudo systemctl restart roborakshak.service
sudo journalctl -u roborakshak.service -f
```

## Troubleshooting

1. Service fails to start:
```bash
sudo journalctl -u roborakshak.service -n 100
```

2. GPIO permission issues:
```bash
sudo usermod -a -G gpio $USER
sudo reboot
```

3. UI not reachable:
- confirm Pi IP using `hostname -I`
- confirm service is running
- confirm port `5000` is accessible on your network

## Known Current Mismatches

These are documented so behavior is clear without changing code in this pass.

1. `config.ini` is present but not read by `backend/app.py`.
   - Runtime values (GPIO pins, host, port, defaults) are currently hardcoded in code.

2. Motor control implementation currently reflects the logic in `backend/app.py` exactly.
   - Wiring/behavior expectations should be validated on hardware before production use.
