# Development Guide

## Local Setup

```bash
git clone https://github.com/abh-awasthi/roborakshak.git
cd roborakshak
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 backend/app.py
```

Open `http://localhost:5000`.

## Runtime Model

- Backend: Flask app in `backend/app.py`
- Frontend: static HTML/CSS/JS under `frontend/`
- No build step for frontend

## API Contract (Current)

- `POST /api/motor/forward`
- `POST /api/motor/backward`
- `POST /api/motor/left`
- `POST /api/motor/right`
- `POST /api/motor/stop`
- `POST /api/motor/speed/<int:speed>`
- `GET /api/status`

Example:

```bash
curl -X POST http://localhost:5000/api/motor/forward
curl -X POST http://localhost:5000/api/motor/speed/40
curl http://localhost:5000/api/status
```

## GPIO and Mock Mode

`backend/app.py` tries to import `RPi.GPIO`. If unavailable, it falls back to mock GPIO.

Force mock mode:

```bash
FORCE_MOCK=1 python3 backend/app.py
```

## High-Value Files

- `backend/app.py`: routes, GPIO init, movement methods, status
- `frontend/static/script.js`: client commands and polling
- `frontend/index.html`: control surface markup
- `install.sh`: installer and service creation logic

## Known Current Mismatches

1. `config.ini` is not wired into runtime config.
2. `install.sh` path derivation can target parent directory of repo.

## Validation Checklist

1. Start app locally and load UI.
2. Verify button clicks hit expected API routes.
3. Verify `GET /api/status` returns `speed` and `direction`.
4. Verify mock banner appears when `FORCE_MOCK=1`.
