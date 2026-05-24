#!/bin/bash

# RoboRakshak Installation Verification Script
# Run this after installation to verify everything is working

set -e

echo "=========================================="
echo "RoboRakshak Installation Verification"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check 1: Project files exist
echo -e "${YELLOW}Checking project files...${NC}"
files_ok=true
for file in backend/app.py frontend/index.html requirements.txt install.sh; do
    if [ -f "$SCRIPT_DIR/$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${RED}✗${NC} $file (MISSING)"
        files_ok=false
    fi
done
echo ""

# Check 2: Virtual environment
echo -e "${YELLOW}Checking virtual environment...${NC}"
if [ -d "$SCRIPT_DIR/venv" ]; then
    echo -e "${GREEN}✓${NC} Virtual environment found"
else
    echo -e "${YELLOW}⚠${NC} Virtual environment not created yet (will be created by install.sh)"
fi
echo ""

# Check 3: Python dependencies
if [ -d "$SCRIPT_DIR/venv" ]; then
    echo -e "${YELLOW}Checking Python dependencies...${NC}"
    source "$SCRIPT_DIR/venv/bin/activate"
    
    deps=("flask" "RPi.GPIO" "cv2" "numpy")
    for dep in "${deps[@]}"; do
        if python3 -c "import $dep" 2>/dev/null; then
            echo -e "${GREEN}✓${NC} $dep installed"
        else
            echo -e "${RED}✗${NC} $dep (NOT INSTALLED)"
        fi
    done
    echo ""
fi

# Check 4: Systemd service
echo -e "${YELLOW}Checking systemd service...${NC}"
if [ -f "/etc/systemd/system/roborakshak.service" ]; then
    echo -e "${GREEN}✓${NC} Service file exists"
    
    if systemctl is-enabled roborakshak.service &> /dev/null; then
        echo -e "${GREEN}✓${NC} Service is enabled"
    else
        echo -e "${YELLOW}⚠${NC} Service is not enabled"
    fi
    
    if systemctl is-active --quiet roborakshak.service; then
        echo -e "${GREEN}✓${NC} Service is running"
    else
        echo -e "${RED}✗${NC} Service is not running"
    fi
else
    echo -e "${YELLOW}⚠${NC} Systemd service not configured (will be created by install.sh)"
fi
echo ""

# Check 5: Port availability
echo -e "${YELLOW}Checking port 5000...${NC}"
if command -v lsof &> /dev/null; then
    if lsof -i :5000 &> /dev/null; then
        echo -e "${GREEN}✓${NC} Port 5000 is in use (service running)"
    else
        echo -e "${YELLOW}⚠${NC} Port 5000 is available (service not running)"
    fi
else
    echo -e "${YELLOW}⚠${NC} lsof not available, skipping port check"
fi
echo ""

# Check 6: Network interface
echo -e "${YELLOW}Checking network interfaces...${NC}"
if command -v hostname &> /dev/null; then
    IP=$(hostname -I 2>/dev/null | awk '{print $1}')
    if [ -n "$IP" ]; then
        echo -e "${GREEN}✓${NC} Raspberry Pi IP: $IP"
        echo "   Access control panel at: http://$IP:5000"
    else
        echo -e "${YELLOW}⚠${NC} Could not determine IP address"
    fi
else
    echo -e "${YELLOW}⚠${NC} hostname command not available"
fi
echo ""

# Check 7: GPIO access
echo -e "${YELLOW}Checking GPIO access...${NC}"
if [ -e "/dev/gpiomem" ]; then
    echo -e "${GREEN}✓${NC} /dev/gpiomem exists"
    
    if [ -r "/dev/gpiomem" ] && [ -w "/dev/gpiomem" ]; then
        echo -e "${GREEN}✓${NC} GPIO permissions OK"
    else
        echo -e "${YELLOW}⚠${NC} GPIO permissions may be restricted"
        echo "   Run: sudo usermod -a -G gpio \$USER"
    fi
else
    echo -e "${RED}✗${NC} /dev/gpiomem not found"
fi
echo ""

# Check 8: Service logs
if [ -d "/var/log" ]; then
    echo -e "${YELLOW}Recent service logs:${NC}"
    if command -v journalctl &> /dev/null; then
        echo ""
        sudo journalctl -u roborakshak.service -n 5 --no-pager 2>/dev/null || echo "   (No logs available yet)"
    fi
fi
echo ""

# Final summary
echo "=========================================="
echo "Verification Summary"
echo "=========================================="
echo ""

if [ "$files_ok" = true ]; then
    echo -e "${GREEN}✓${NC} Project files are in place"
    echo ""
    echo "Next steps:"
    echo "1. Run installation: sudo bash install.sh"
    echo "2. Wait for completion (5-10 minutes)"
    echo "3. Open control panel: http://<your-pi-ip>:5000"
    echo "4. Test motor controls"
    echo ""
    echo "For help:"
    echo "- View logs: sudo journalctl -u roborakshak.service -f"
    echo "- Check service: sudo systemctl status roborakshak.service"
    echo "- See README.md for detailed instructions"
else
    echo -e "${RED}✗${NC} Some project files are missing"
    echo ""
    echo "Please ensure you have the complete repository:"
    echo "git clone https://github.com/abh-awasthi/roborakshak.git"
fi

echo ""
echo "=========================================="
