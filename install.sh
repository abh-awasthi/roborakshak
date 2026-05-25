#!/bin/bash

# RoboRakshak Automatic Installation Script for Raspberry Pi
# This script will install all dependencies and set up the application to run automatically

set -e

echo "=========================================="
echo "RoboRakshak Automatic Installation"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo -e "${YELLOW}Warning: This doesn't appear to be a Raspberry Pi${NC}"
    echo "Continuing anyway..."
    echo ""
fi

# Get current user
CURRENT_USER=$(whoami)
if [ "$CURRENT_USER" = "root" ]; then
    echo -e "${YELLOW}Running as root. This is not recommended.${NC}"
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$SCRIPT_DIR"

echo -e "${GREEN}Project Directory: $PROJECT_DIR${NC}"
echo -e "${GREEN}Installation User: $CURRENT_USER${NC}"
echo ""

# Step 1: Update system packages
echo -e "${YELLOW}Step 1: Updating system packages...${NC}"
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv git
echo -e "${GREEN}✓ System packages updated${NC}"
echo ""

# Step 2: Create virtual environment
echo -e "${YELLOW}Step 2: Creating Python virtual environment...${NC}"
if [ ! -d "$PROJECT_DIR/venv" ]; then
    python3 -m venv "$PROJECT_DIR/venv"
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi
echo ""

# Step 3: Activate virtual environment and install dependencies
echo -e "${YELLOW}Step 3: Installing Python dependencies...${NC}"
source "$PROJECT_DIR/venv/bin/activate"
pip install --upgrade pip setuptools wheel
pip install -r "$PROJECT_DIR/requirements.txt"
echo -e "${GREEN}✓ Python dependencies installed${NC}"
echo ""

# Step 4: Create systemd service file
echo -e "${YELLOW}Step 4: Creating systemd service...${NC}"
SERVICE_FILE="/etc/systemd/system/roborakshak.service"

sudo tee "$SERVICE_FILE" > /dev/null << EOF
[Unit]
Description=RoboRakshak Motor Control Service
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$PROJECT_DIR/backend
Environment="PATH=$PROJECT_DIR/venv/bin"
# Set FORCE_MOCK=1 to force mock GPIO (useful for testing without hardware)
Environment="FORCE_MOCK=0"
ExecStart=$PROJECT_DIR/venv/bin/python3 app.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✓ Service file created at $SERVICE_FILE${NC}"
echo ""

# Step 5: Enable and start service
echo -e "${YELLOW}Step 5: Enabling and starting RoboRakshak service...${NC}"
sudo systemctl daemon-reload
sudo systemctl enable roborakshak.service
sudo systemctl start roborakshak.service

echo -e "${GREEN}✓ Service enabled and started${NC}"
echo ""

# Step 6: Verify service status
echo -e "${YELLOW}Step 6: Verifying service status...${NC}"
sleep 2
if sudo systemctl is-active --quiet roborakshak.service; then
    echo -e "${GREEN}✓ RoboRakshak service is running${NC}"
else
    echo -e "${RED}✗ RoboRakshak service failed to start${NC}"
    echo "Check logs with: sudo journalctl -u roborakshak.service -n 50"
fi
echo ""

# Step 7: Create helpful commands file
echo -e "${YELLOW}Step 7: Creating helpful commands reference...${NC}"
COMMANDS_FILE="$PROJECT_DIR/INSTALLATION_COMMANDS.md"

cat > "$COMMANDS_FILE" << 'EOF'
# RoboRakshak Useful Commands

## Service Management
```bash
# Check service status
sudo systemctl status roborakshak.service

# Start the service
sudo systemctl start roborakshak.service

# Stop the service
sudo systemctl stop roborakshak.service

# Restart the service
sudo systemctl restart roborakshak.service

# Disable auto-start (service won't start on boot)
sudo systemctl disable roborakshak.service

# Enable auto-start (service will start on boot)
sudo systemctl enable roborakshak.service
```

## Logs and Debugging
```bash
# View recent logs (last 50 lines)
sudo journalctl -u roborakshak.service -n 50

# View logs in real-time
sudo journalctl -u roborakshak.service -f

# View all logs for the service
sudo journalctl -u roborakshak.service
```

## Manual Execution (for testing)
```bash
# Activate virtual environment
source /path/to/RoboRakshak/venv/bin/activate

# Run the app directly
cd /path/to/RoboRakshak/backend
python3 app.py
```

## Forcing Mock GPIO
You can force the application to use the mock GPIO implementation (good for testing without hardware).

```bash
# Run locally with mock GPIO
FORCE_MOCK=1 python3 app.py

# Or for systemd-managed service (set, then restart)
sudo systemctl set-environment FORCE_MOCK=1
sudo systemctl restart roborakshak.service
```

## Access the Control Panel
```
Open your web browser and go to:
http://<raspberry-pi-ip>:5000

Replace <raspberry-pi-ip> with your Raspberry Pi's IP address.
You can find it with: hostname -I
```

## Update Dependencies
```bash
source /path/to/RoboRakshak/venv/bin/activate
pip install --upgrade -r /path/to/RoboRakshak/requirements.txt
```

## Uninstall Service
```bash
sudo systemctl stop roborakshak.service
sudo systemctl disable roborakshak.service
sudo rm /etc/systemd/system/roborakshak.service
sudo systemctl daemon-reload
```
EOF

echo -e "${GREEN}✓ Commands reference created${NC}"
echo ""

# Final Summary
echo "=========================================="
echo -e "${GREEN}Installation Complete!${NC}"
echo "=========================================="
echo ""
echo "📝 Summary:"
echo "  - Python virtual environment created"
echo "  - Dependencies installed"
echo "  - Systemd service configured"
echo "  - Service set to auto-start on boot"
echo ""
echo "🚀 Access RoboRakshak:"
echo "  - Open browser: http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "📊 Check service status:"
echo "  - sudo systemctl status roborakshak.service"
echo ""
echo "📖 View logs:"
echo "  - sudo journalctl -u roborakshak.service -f"
echo ""
echo "📝 Useful commands saved to: $COMMANDS_FILE"
echo ""
echo "=========================================="
echo "RoboRakshak is running! 🤖"
echo "=========================================="
