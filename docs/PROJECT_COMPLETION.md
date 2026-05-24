# Project Completion Snapshot

This snapshot reflects the repository as of May 2026 and is intentionally aligned to current code.

## Delivered Components

1. Flask backend for motor control in `backend/app.py`
2. Browser control panel in `frontend/`
3. Installer and verification scripts: `install.sh`, `verify-install.sh`
4. Documentation set in `docs/`

## API Delivered

- `POST /api/motor/forward`
- `POST /api/motor/backward`
- `POST /api/motor/left`
- `POST /api/motor/right`
- `POST /api/motor/stop`
- `POST /api/motor/speed/<int:speed>`
- `GET /api/status`

## Runtime Characteristics

- App listens on `0.0.0.0:5000`
- GPIO behavior:
  - uses `RPi.GPIO` when available
  - falls back to mock GPIO when unavailable
  - can force mock mode with `FORCE_MOCK=1`
- Frontend polls status every 2 seconds

## Operational Commands

```bash
sudo bash install.sh
sudo systemctl status roborakshak.service
sudo journalctl -u roborakshak.service -f
```

## Known Current Mismatches

1. `install.sh` currently derives `PROJECT_DIR` as parent directory of script path.
   - This can produce incorrect service and venv paths depending on repo location.

2. `config.ini` is present but not used by backend runtime.
   - Runtime values are hardcoded in `backend/app.py`.

## Reference Docs

- [QUICKSTART.md](QUICKSTART.md)
- [INSTALLATION.md](INSTALLATION.md)
- [SETUP.md](SETUP.md)
- [DEVELOPMENT.md](DEVELOPMENT.md)
