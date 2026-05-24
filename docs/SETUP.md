# RoboRakshak Automatic Installation Setup

## What Gets Installed

### System Packages
- Python 3 with pip
- Git
- Python development headers

### Python Packages
- Flask 2.3.2 - Web framework
- Flask-CORS 4.0.0 - Cross-origin requests
- RPi.GPIO 0.7.0 - GPIO control
- OpenCV 4.8.0.74 - Computer vision (for future use)
- picamera2 0.3.12 - Camera interface
- numpy 1.24.3 - Numerical computing
- Werkzeug & Jinja2 - Flask dependencies

### System Configuration
- Python virtual environment in `./venv`
- Systemd service at `/etc/systemd/system/roborakshak.service`
- Auto-start enabled (runs on boot)
- Automatic restart on failure

---

## Installation Steps

The `install.sh` script performs these steps automatically:

1. **System Update**
   - `sudo apt-get update`
   - Install Python 3 and pip
   - Install git

2. **Virtual Environment**
   - Create isolated Python environment
   - Prevents conflicts with system Python

3. **Dependencies**
   - Install packages from `requirements.txt`
   - Create isolated dependencies

4. **Systemd Service**
   - Create service file
   - Configure to run as current user
   - Set working directory to `backend/`

5. **Enable & Start**
   - Enable service to auto-start on boot
   - Start service immediately
   - Verify service is running

6. **Documentation**
   - Generate helpful commands reference
   - Create logs directory

---

## Post-Installation

### First Run Checklist
- [ ] Access control panel at `http://<ip>:5000`
- [ ] Test forward/backward movement
- [ ] Test left/right turning
- [ ] Test speed slider
- [ ] Check keyboard controls
- [ ] Verify service auto-starts after reboot

### Ongoing Maintenance
- Monitor logs regularly: `sudo journalctl -u roborakshak.service -f`
- Update dependencies monthly: `pip install --upgrade -r requirements.txt`
- Check for GitHub updates: `git pull` (if installed via git)

### Performance Optimization
- Service runs with standard priority
- GPIO operations are hardware-accelerated
- Web UI is responsive and lightweight
- Motor status updates every 2 seconds

---

## Security Notes

⚠️ **Important Security Considerations**

1. **GPIO Access**: The service runs as a regular user. Ensure your user account has GPIO access:
   ```bash
   sudo usermod -a -G gpio $USER
   sudo usermod -a -G dialout $USER
   ```

2. **Network Access**: The web interface is accessible to anyone on your network by default.
   - Consider using a firewall to restrict access
   - Or add authentication (coming in future release)

3. **Logs**: Service logs are accessible via journalctl

---

## Troubleshooting Installation

### GPIO Permission Issues
```bash
# Solution:
sudo usermod -a -G gpio $USER
sudo chmod g+rw /dev/gpiomem
sudo reboot
```

### Service Fails to Start
```bash
# Check error:
sudo journalctl -u roborakshak.service -n 50

# Possible causes:
# - GPIO pins already in use
# - Python path issues
# - Missing dependencies
```

### Python Module Not Found
```bash
# Reinstall dependencies:
source venv/bin/activate
pip install -r requirements.txt
```

### Port Already in Use
The service uses port 5000. If it's in use:
1. Edit `/etc/systemd/system/roborakshak.service`
2. Change `app.py` parameters to use different port
3. Restart service: `sudo systemctl restart roborakshak.service`

---

## Uninstalling

To completely remove RoboRakshak:

```bash
# Stop and disable service
sudo systemctl stop roborakshak.service
sudo systemctl disable roborakshak.service

# Remove service file
sudo rm /etc/systemd/system/roborakshak.service

# Reload systemd
sudo systemctl daemon-reload

# Remove installation directory (optional)
rm -rf ~/roborakshak

# Clean up Python environment (optional)
rm -rf ~/roborakshak/venv
```

---

## Reference

For detailed information, see:
- [INSTALLATION.md](INSTALLATION.md) - Installation guide
- [ARCHITECTURE.md](ARCHITECTURE.md) - Project architecture
- [API_PLAN.md](API_PLAN.md) - API endpoints
- [CONTEXT.md](CONTEXT.md) - Project context
