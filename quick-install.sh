#!/bin/bash

# Quick Installation Script for RoboRakshak
# This is a simplified version that just runs the main installer

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Starting RoboRakshak Installation..."
echo ""

# Check if the main installer exists
if [ ! -f "$SCRIPT_DIR/install.sh" ]; then
    echo "Error: install.sh not found!"
    exit 1
fi

# Run the installer with bash
bash "$SCRIPT_DIR/install.sh"
