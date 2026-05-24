# Setup Details

This page describes the current setup behavior in this repository.

## Dependencies

From `requirements.txt`:
- Flask
- flask-cors
- RPi.GPIO
- opencv-python
- picamera2
- numpy
- Werkzeug
- Jinja2

## Installer Behavior (`install.sh`)

`install.sh` currently:
1. updates apt packages
2. installs `python3-pip`, `python3-venv`, `git`
3. creates `venv`
4. installs Python requirements
5. creates `/etc/systemd/system/roborakshak.service`
6. enables and starts `roborakshak.service`

## Runtime Entry Point

- Application process: `python3 backend/app.py`
- Flask listens on `0.0.0.0:5000` (hardcoded in code)

## systemd Notes

The generated service includes:
- `WorkingDirectory=$PROJECT_DIR/backend`
- `ExecStart=$PROJECT_DIR/venv/bin/python3 app.py`
- `Environment="FORCE_MOCK=0"`

Useful commands:

```bash
sudo systemctl status roborakshak.service
sudo systemctl restart roborakshak.service
sudo journalctl -u roborakshak.service -f
```

## FORCE_MOCK

Set mock GPIO explicitly:

```bash
FORCE_MOCK=1 python3 backend/app.py
```

For running service:

```bash
sudo systemctl set-environment FORCE_MOCK=1
sudo systemctl restart roborakshak.service
```

## Known Current Mismatches

1. `install.sh` computes `PROJECT_DIR` as parent of script directory.
   - Because `install.sh` is in repo root, this can point one level above repo and affect generated paths.

2. `config.ini` is not currently read by backend runtime.
   - Runtime values come from `backend/app.py`.
