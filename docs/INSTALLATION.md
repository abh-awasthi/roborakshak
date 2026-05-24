# RoboRakshak - Motor Control Installation Guide

## Quick Start (Automatic Installation)

### On Raspberry Pi:

```bash
# Download the repository
git clone https://github.com/abh-awasthi/roborakshak.git
cd roborakshak

# Make the installer executable (if needed)
chmod +x install.sh

# Run the automatic installer
sudo bash install.sh
```

That's it! The installer will:
1. ✅ Update system packages
2. ✅ Create a Python virtual environment
3. ✅ Install all dependencies
4. ✅ Configure systemd service to auto-start on boot
5. ✅ Start the RoboRakshak service immediately

### Access the Control Panel

Once installed, open your web browser and go to:
```
http://<your-raspberry-pi-ip>:5000
```

To find your Raspberry Pi's IP address, run:
```bash
hostname -I
```

---

## Features

### Motor Control
- **Speed Control**: Adjust motor speed from 0-100% using a slider
- **Preset Speeds**: Quick buttons for 25%, 50%, 75%, and 100%
- **Direction Control**: Forward, Backward, Left Turn, Right Turn
- **Emergency Stop**: Red stop button for immediate halt

### User Interface
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Real-time Status**: Speed, direction, and connection status updates
- **Keyboard Controls**: 
  - ↑ Forward, ↓ Backward, ← Left, → Right
  - Space = Stop
  - +/- = Adjust Speed

### Automatic Startup
- Service automatically starts on Raspberry Pi boot
- Self-healing: Service restarts if it crashes
- Logging: All activity logged to systemd journal

---

## System Service Commands

### Check Status
```bash
sudo systemctl status roborakshak.service
```

### View Logs
```bash
# Last 50 lines
sudo journalctl -u roborakshak.service -n 50

# Real-time logs
sudo journalctl -u roborakshak.service -f

# All logs
sudo journalctl -u roborakshak.service
```

### Manage Service
```bash
# Start service
sudo systemctl start roborakshak.service

# Stop service
sudo systemctl stop roborakshak.service

# Restart service
sudo systemctl restart roborakshak.service

# Enable auto-start on boot
sudo systemctl enable roborakshak.service

# Disable auto-start
sudo systemctl disable roborakshak.service
```

---

## Manual Installation (Alternative)

If you prefer to install manually:

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the application
cd backend
python3 app.py

# 4. Open browser to http://localhost:5000
```

---

## Troubleshooting

### Service Won't Start
```bash
# Check for errors
sudo journalctl -u roborakshak.service -n 100

# Verify GPIO permissions (if getting GPIO errors)
sudo usermod -a -G gpio $USER
sudo reboot
```

### Can't Access Control Panel
1. Check Raspberry Pi IP: `hostname -I`
2. Verify service is running: `sudo systemctl status roborakshak.service`
3. Check firewall isn't blocking port 5000
4. Try `http://<ip>:5000` instead of hostname

### GPIO Permission Denied
```bash
# Add user to gpio group
sudo usermod -a -G gpio $USER
sudo chmod g+rw /dev/gpiomem
```

### Application Crashes
1. Check logs: `sudo journalctl -u roborakshak.service -f`
2. Verify all required packages: `pip list`
3. Check GPIO pin conflicts with other applications

---

## API Endpoints

The backend provides REST API endpoints:

```
POST /api/motor/forward      - Move forward
POST /api/motor/backward     - Move backward
POST /api/motor/left         - Turn left
POST /api/motor/right        - Turn right
POST /api/motor/stop         - Stop all motors
POST /api/motor/speed/<0-100> - Set speed (0-100%)
GET  /api/status             - Get current status
```

---

## Hardware Configuration

GPIO Pin Mapping:
- GPIO 5, 6   → Left Motor (IN1, IN2)
- GPIO 13, 19 → Right Motor (IN3, IN4)

Power Requirements:
- 12V Battery → L298N Motor Driver
- LM2596 Voltage Regulator → Raspberry Pi (5V, 3A)
- Shared Ground between Pi and L298N

---

## File Structure

```
roborakshak/
├── backend/
│   └── app.py                 # Flask backend
├── frontend/
│   ├── index.html             # Main control panel
│   └── static/
│       ├── style.css          # UI styles
│       └── script.js          # Control logic
├── venv/                      # Python environment (created after install)
├── requirements.txt           # Python dependencies
├── install.sh                 # Automatic installer
└── README.md                  # This file
```

---

## Need Help?

1. **Check logs**: `sudo journalctl -u roborakshak.service -f`
2. **Review installation**: `cat /etc/systemd/system/roborakshak.service`
3. **Test GPIO access**: `python3 -c "import RPi.GPIO as GPIO"`

---

## License

This project is part of RoboRakshak - AI-Powered Home Security Robot

Enjoy controlling your robot! 🤖
