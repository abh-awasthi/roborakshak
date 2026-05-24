# Quick Start Guide

## 30-Second Installation

```bash
git clone https://github.com/abh-awasthi/roborakshak.git
cd roborakshak
sudo bash install.sh
```

That's it! Your RoboRakshak will be running in 5-10 minutes.

---

## Access Control Panel

Open your browser:
```
http://<your-pi-ip>:5000
```

To find your Pi's IP:
```bash
hostname -I
```

---

## Control Methods

### Mouse/Touch
- Click direction buttons
- Drag speed slider
- Click preset buttons

### Keyboard
- ↑↓←→ = Control direction
- SPACE = Stop
- +/- = Adjust speed

---

## Check It's Working

```bash
sudo systemctl status roborakshak.service
```

Should show: **Active (running)**

---

## View Logs

```bash
sudo journalctl -u roborakshak.service -f
```

---

## Need Help?

- **Can't access UI?** Check: `sudo systemctl status roborakshak.service`
- **Motors not responding?** Check: `sudo journalctl -u roborakshak.service -f`
- **GPIO errors?** Run: `sudo usermod -a -G gpio $USER` then reboot

---

## Full Documentation

- [README.md](README.md) - Complete overview
- [INSTALLATION.md](INSTALLATION.md) - Detailed setup
- [DEVELOPMENT.md](DEVELOPMENT.md) - Code guide
- [API_PLAN.md](API_PLAN.md) - API reference

---

**Enjoy! 🤖**
