# RoboRakshak - AI-Powered Home Security Robot
## Motor Control System with Automatic Installation

![RoboRakshak](https://img.shields.io/badge/RoboRakshak-AI%20Security%20Robot-blue)
![Status](https://img.shields.io/badge/Status-Active%20Development-green)
![Python](https://img.shields.io/badge/Python-3.7%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

### 🚀 Quick Start

On your Raspberry Pi:

```bash
git clone https://github.com/abh-awasthi/roborakshak.git
cd roborakshak
sudo bash install.sh
```

Then open your browser to: `http://<raspberry-pi-ip>:5000`

---

## ✨ Features

### Motor Control Interface
- **🎮 Direction Control**: Forward, Backward, Left, Right, Stop
- **⚡ Speed Control**: 0-100% adjustable speed with preset buttons
- **⌨️ Keyboard Controls**: Arrow keys + Space for intuitive control
- **📱 Responsive Design**: Works on desktop, tablet, and mobile
- **🎯 Touch-friendly**: Large buttons optimized for touch interface

### Automatic Installation
- **🔧 One-Command Setup**: Single `install.sh` for complete installation
- **♻️ Auto-Start on Boot**: Service starts automatically with Raspberry Pi
- **🛡️ Self-Healing**: Service automatically restarts if it crashes
- **📊 Integrated Logging**: All activity logged to systemd journal

### Real-Time Status
- Connection status monitoring
- Live speed and direction display
- Command history
- System response feedback

---

## 📋 System Requirements

### Hardware
- **Raspberry Pi 4 Model B** (or compatible)
- **L298N Motor Driver**
- **12V DC Motors** (or equivalent)
- **12V Battery** with LM2596 voltage regulator
- **Jumper wires and breadboard**

### Software Requirements
- Raspberry Pi OS (Buster or newer)
- Internet connection for initial setup
- Git (automatically installed)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│        Web Browser / UI (Port 5000)      │
│   - HTML5 + CSS3 + JavaScript           │
│   - Mobile-responsive design            │
│   - Real-time status updates            │
└────────────────┬────────────────────────┘
                 │
                 ▼ HTTP REST API
┌─────────────────────────────────────────┐
│   Flask Web Server (Python)             │
│   - Motor control endpoints             │
│   - Speed regulation                    │
│   - Direction management                │
└────────────────┬────────────────────────┘
                 │
                 ▼ GPIO Control
┌─────────────────────────────────────────┐
│   RPi GPIO (BCM Mode)                   │
│   - PWM control at 50Hz                 │
│   - Pin configuration                   │
└────────────────┬────────────────────────┘
                 │
                 ▼ Hardware Control
┌─────────────────────────────────────────┐
│   L298N Motor Driver                    │
│   - Dual H-bridge motor driver          │
│   - PWM speed control                   │
│   - Bidirectional control               │
└────────────────┬────────────────────────┘
                 │
                 ▼
      ┌──────────────────────┐
      │  Left Motor          │
      │  Right Motor         │
      │  Additional Features │
      └──────────────────────┘
```

### GPIO Pin Configuration

| Component | GPIO | Function |
|-----------|------|----------|
| Left Motor - Pin 1 | GPIO 5 | IN1 (Motor A) |
| Left Motor - Pin 2 | GPIO 6 | IN2 (Motor A) |
| Right Motor - Pin 1 | GPIO 13 | IN3 (Motor B) |
| Right Motor - Pin 2 | GPIO 19 | IN4 (Motor B) |

---

## 🎮 Control Interface

### Web Interface Features
- **Directional D-Pad**: Large buttons for intuitive control
- **Speed Slider**: Smooth, responsive speed adjustment
- **Preset Speeds**: Quick access to 25%, 50%, 75%, 100%
- **Real-time Feedback**: Instant status updates
- **Error Handling**: Connection status and automatic reconnection

### Keyboard Shortcuts
| Key | Action |
|-----|--------|
| `↑` Arrow Up | Move Forward |
| `↓` Arrow Down | Move Backward |
| `←` Arrow Left | Turn Left |
| `→` Arrow Right | Turn Right |
| `SPACE` | Emergency Stop |
| `+` | Increase Speed (5% increment) |
| `-` | Decrease Speed (5% decrement) |

---

## 📡 API Endpoints

### Motor Control
```bash
# Move Forward (at current speed)
POST /api/motor/forward

# Move Backward
POST /api/motor/backward

# Turn Left
POST /api/motor/left

# Turn Right
POST /api/motor/right

# Stop All Motors
POST /api/motor/stop

# Set Speed (0-100)
POST /api/motor/speed/<speed>

# Get Current Status
GET /api/status
```

### Response Format
```json
{
  "status": "moving forward",
  "speed": 50,
  "direction": "forward"
}
```

---

## 🔧 Installation Details

### What Gets Installed

#### System Packages
- Python 3 & pip
- Git
- Python development headers

#### Python Modules
- **Flask** - Web framework
- **RPi.GPIO** - GPIO control
- **OpenCV** - Computer vision (for future features)
- **picamera2** - Camera support
- **numpy** - Numerical computing

#### System Configuration
- Python virtual environment
- Systemd service file
- Auto-start on boot
- Automatic crash recovery

### Installation Steps (Automated)

1. **System packages update** ✓
2. **Python virtual environment creation** ✓
3. **Dependency installation** ✓
4. **Systemd service configuration** ✓
5. **Service enable & start** ✓

---

## 🚀 Usage Guide

### Basic Operation

1. **Access Control Panel**
   ```
   Open browser: http://<raspberry-pi-ip>:5000
   ```

2. **Find Your Pi's IP Address**
   ```bash
   hostname -I
   ```

3. **Control the Robot**
   - Use buttons or keyboard controls
   - Adjust speed with slider or preset buttons
   - Watch real-time status updates

### Advanced Operations

#### Check Service Status
```bash
sudo systemctl status roborakshak.service
```

#### View Live Logs
```bash
sudo journalctl -u roborakshak.service -f
```

#### Restart Service
```bash
sudo systemctl restart roborakshak.service
```

#### Stop Service
```bash
sudo systemctl stop roborakshak.service
```

---

## 🐛 Troubleshooting

### Service Won't Start
```bash
# Check logs for errors
sudo journalctl -u roborakshak.service -n 100

# Common issues:
# 1. GPIO already in use
# 2. Python path incorrect
# 3. Port 5000 already in use
```

### Can't Access Web Interface
1. Verify Pi is on network: `ping <pi-ip>`
2. Check service is running: `sudo systemctl status roborakshak.service`
3. Check port: `sudo ss -tlnp | grep 5000`
4. Try different browser

### Motor Not Responding
1. Verify connections
2. Check GPIO permissions: `ls -l /dev/gpiomem`
3. Test GPIO: `python3 -c "import RPi.GPIO as GPIO"`
4. Check logs for errors

### GPIO Permission Denied
```bash
# Add user to GPIO group
sudo usermod -a -G gpio $USER
sudo chmod g+rw /dev/gpiomem
# Restart for changes to take effect
```

---

## 📁 File Structure

```
roborakshak/
├── backend/
│   └── app.py                    # Flask application with motor control
├── frontend/
│   ├── index.html               # Web UI main page
│   └── static/
│       ├── style.css            # Responsive styling
│       └── script.js            # Control logic and API calls
├── docs/                        # Documentation folder
│   ├── QUICKSTART.md            # Quick start guide
│   ├── INSTALLATION.md          # Detailed installation guide
│   ├── DEVELOPMENT.md           # Developer guide
│   ├── API_PLAN.md              # API documentation
│   ├── SETUP.md                 # Setup information
│   ├── PROJECT_COMPLETION.md    # Project summary
│   ├── ARCHITECTURE.md          # System architecture
│   ├── CONTEXT.md               # Project context
│   ├── FEATURES.md              # Feature list
│   ├── ROADMAP.md               # Project roadmap
│   ├── AI_ROADMAP.md            # AI features roadmap
│   └── TROUBLESHOOTING.md       # Troubleshooting guide
├── venv/                        # Python virtual environment (created by install)
├── config.ini                   # Configuration file
├── requirements.txt             # Python dependencies
├── install.sh                   # Automatic installation script
├── README.md                    # Main documentation (this file)
└── LICENSE                      # Project license
```

---

## 🔐 Security Considerations

- **Local Network Only**: Currently accessible to all devices on your network
- **GPIO Access**: Service runs with limited user permissions
- **Port 5000**: Standard Flask development port (can be changed)
- **Future**: Authentication and encryption coming in v2.0

### Securing Your Installation
```bash
# Restrict to localhost only (edit /etc/systemd/system/roborakshak.service)
# Change: ExecStart=/path/to/app.py
# To: ExecStart=/path/to/app.py --host 127.0.0.1

# Or use a firewall
sudo ufw allow 5000/tcp
sudo ufw enable
```

---

## 📊 Performance Specs

- **Response Time**: < 100ms for motor commands
- **Status Updates**: 2 per second (configurable)
- **Motor Control**: 50Hz PWM frequency
- **Max Speed**: 100% (configurable per motor)
- **Weight**: Lightweight (< 20MB installation)

---

## 🚢 Deployment

### Production Deployment
For production deployment, consider:

1. **Nginx Reverse Proxy**
   - SSL/TLS encryption
   - Load balancing
   - Static file serving

2. **Gunicorn Application Server**
   - Multiple worker processes
   - Better stability than Flask development server
   - Production WSGI server

3. **Systemd Hardening**
   - Resource limits
   - Capability restrictions
   - Security context settings

---

## 🛣️ Roadmap

### Phase 1 (Current) ✅
- [x] Motor speed control
- [x] Motor direction control
- [x] Web-based UI
- [x] Keyboard controls
- [x] Automatic installation
- [x] Auto-start service

### Phase 2 (Soon)
- [ ] Camera live streaming
- [ ] Motion detection
- [ ] Mobile app
- [ ] Authentication/JWT
- [ ] HTTPS/SSL support

### Phase 3 (Future)
- [ ] Face recognition
- [ ] Autonomous patrol
- [ ] Cloud integration
- [ ] Voice assistant
- [ ] Smart home integration

### Phase 4 (Long-term)
- [ ] AI-powered surveillance
- [ ] Intruder detection
- [ ] Multi-robot coordination
- [ ] Desktop application
- [ ] Product launch

---

## 📝 API Documentation

Full API documentation available in [API_PLAN.md](docs/API_PLAN.md)

### Quick Example

```javascript
// Control motors via API
const baseURL = 'http://raspberry-pi-ip:5000';

// Move forward
fetch(baseURL + '/api/motor/forward', { method: 'POST' });

// Set speed to 75%
fetch(baseURL + '/api/motor/speed/75', { method: 'POST' });

// Stop
fetch(baseURL + '/api/motor/stop', { method: 'POST' });

// Get status
fetch(baseURL + '/api/status').then(r => r.json());
```

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a pull request

---

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details

---

## 👨‍💻 Author

**Abhishek Awasthi**
- GitHub: [@abh-awasthi](https://github.com/abh-awasthi)

---

## 🙋 Support

For issues, questions, or suggestions:
1. Check [Troubleshooting](#-troubleshooting) section
2. Review logs: `sudo journalctl -u roborakshak.service -f`
3. Open a GitHub issue
4. Check project documentation

---

## 🎓 Learning Resources

- **GPIO Control**: [RPi.GPIO Documentation](https://sourceforge.net/projects/raspberry-gpio-python/)
- **Flask**: [Flask Official Guide](https://flask.palletsprojects.com/)
- **L298N Driver**: [L298N Datasheet](https://www.datasheetspdf.com/pdf/L298N)
- **PWM**: [Understanding PWM](https://en.wikipedia.org/wiki/Pulse-width_modulation)

---

## 🏆 Credits

Built with ❤️ for home security automation

**Tech Stack:**
- Python 3
- Flask
- RPi.GPIO
- HTML5
- CSS3
- Vanilla JavaScript

---

**Happy Robot Building! 🤖**

*Last Updated: May 2026*
*Version: 1.0.0*
