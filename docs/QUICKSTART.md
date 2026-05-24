# Quick Start

## Raspberry Pi Install (Fastest Path)

```bash
git clone https://github.com/abh-awasthi/roborakshak.git
cd roborakshak
sudo bash install.sh
```

Then open:

```text
http://<your-pi-ip>:5000
```

Find Pi IP:

```bash
hostname -I
```

## Local Development Run

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 backend/app.py
```

Open `http://localhost:5000`.

## Control API (Current)

- `POST /api/motor/forward|backward|left|right|stop`
- `POST /api/motor/speed/<int:speed>`
- `GET /api/status`

## FORCE_MOCK

Use mock GPIO explicitly:

```bash
FORCE_MOCK=1 python3 backend/app.py
```

## Health Checks

```bash
sudo systemctl status roborakshak.service
sudo journalctl -u roborakshak.service -f
```

## Known Current Mismatch

`install.sh` currently calculates `PROJECT_DIR` as parent of the script directory.  
This may create service/venv paths that do not match the repo root in some layouts.
