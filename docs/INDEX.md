# Documentation Index

## Start Here

- [QUICKSTART.md](QUICKSTART.md): fastest install and first run
- [INSTALLATION.md](INSTALLATION.md): canonical install/run flow and troubleshooting
- [SETUP.md](SETUP.md): installer and service behavior details

## Build and Code

- [DEVELOPMENT.md](DEVELOPMENT.md): local dev workflow and API contract
- [ARCHITECTURE.md](ARCHITECTURE.md): architecture overview
- [API_PLAN.md](API_PLAN.md): API planning notes

## Project Context

- [CONTEXT.md](CONTEXT.md)
- [PROJECT_STATUS.md](PROJECT_STATUS.md)
- [PROJECT_COMPLETION.md](PROJECT_COMPLETION.md)

## Hardware and Ops

- [HARDWARE_SETUP.md](HARDWARE_SETUP.md)
- [SOFTWARE_SETUP.md](SOFTWARE_SETUP.md)
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## Product and Future

- [FEATURES.md](FEATURES.md)
- [ROADMAP.md](ROADMAP.md)
- [AI_ROADMAP.md](AI_ROADMAP.md)
- [FUTURE_IDEAS.md](FUTURE_IDEAS.md)

## Current Runtime Truth

- Backend entrypoint: `backend/app.py`
- API routes are those in `backend/app.py`
- Mock GPIO fallback is automatic when `RPi.GPIO` import fails
- `FORCE_MOCK=1` forces mock mode
- `config.ini` is currently not consumed by runtime code
