# RoboRakshak

RoboRakshak is a Flask-based web controller for a Raspberry Pi robot motor setup.

## Current Scope

- Web control UI for movement and speed
- REST API for motor commands
- Raspberry Pi GPIO runtime with automatic mock fallback
- Live camera streaming, snapshots, and OpenCV motion alerts
- Installer and systemd service setup scripts

## Quick Start

```bash
git clone https://github.com/abh-awasthi/roborakshak.git
cd roborakshak
sudo bash install.sh
```

Then open:

```text
http://<raspberry-pi-ip>:5000
```

## Local Run

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 backend/app.py
```

Open `http://localhost:5000`.

## FORCE_MOCK

`backend/app.py` uses mock GPIO automatically if `RPi.GPIO` import is unavailable.

Force mock mode manually:

```bash
FORCE_MOCK=1 python3 backend/app.py
```

For systemd runtime override:

```bash
sudo systemctl set-environment FORCE_MOCK=1
sudo systemctl restart roborakshak.service
```

## API (Current)

- `POST /api/motor/forward`
- `POST /api/motor/backward`
- `POST /api/motor/left`
- `POST /api/motor/right`
- `POST /api/motor/stop`
- `POST /api/motor/speed/<int:speed>`
- `GET /api/status`
- `GET /api/camera/status`
- `POST /api/camera/motion/start`
- `POST /api/camera/motion/stop`

Example:

```bash
curl -X POST http://localhost:5000/api/motor/forward
curl -X POST http://localhost:5000/api/motor/speed/75
curl http://localhost:5000/api/status
```

## Service Commands

```bash
sudo systemctl status roborakshak.service
sudo systemctl restart roborakshak.service
sudo journalctl -u roborakshak.service -f
```

## Project Layout

```text
backend/app.py
frontend/index.html
frontend/static/script.js
frontend/static/style.css
install.sh
verify-install.sh
requirements.txt
docs/
```

## Known Current Mismatches

1. `install.sh` currently derives `PROJECT_DIR` as the parent of the script directory.
   - Because `install.sh` is in repo root, this can point outside the repo and break generated service/venv paths.

2. `config.ini` exists but is not consumed by `backend/app.py`.
   - Runtime pins, host, and defaults are currently hardcoded in code.

3. Runtime motor behavior is exactly what `backend/app.py` implements today.
   - Validate motion direction and safety on real hardware before production use.

## Documentation

- [Quick Start](docs/QUICKSTART.md)
- [Installation](docs/INSTALLATION.md)
- [Setup](docs/SETUP.md)
- [Development](docs/DEVELOPMENT.md)
- [Documentation Index](docs/INDEX.md)

## License

MIT (see `LICENSE`).
