#!/bin/bash
# APK-Lator Setup Script (Linux)

set -e

echo ""
echo "  ========================================"
echo "     APK-Lator Setup (Linux)"
echo "     Lightweight Android Emulator"
echo "  ========================================"
echo ""

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "  [ERROR] Python 3 not found!"
    echo ""
    echo "  Install via your package manager:"
    echo "    sudo apt install python3 python3-pip python3-venv"
    echo ""
    exit 1
fi

echo "  Python 3 found: $(python3 --version)"
echo ""

# Check/suggest QEMU
if ! command -v qemu-system-x86_64 &> /dev/null; then
    echo "  [WARN] QEMU not found. Installing..."
    if command -v apt &> /dev/null; then
        sudo apt install -y qemu-system-x86 qemu-utils
    elif command -v pacman &> /dev/null; then
        sudo pacman -S --noconfirm qemu-full
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y qemu-system-x86
    else
        echo "  Could not auto-install QEMU. Please install manually."
    fi
fi

# Check/suggest ADB
if ! command -v adb &> /dev/null; then
    echo "  [WARN] ADB not found. Installing..."
    if command -v apt &> /dev/null; then
        sudo apt install -y adb
    elif command -v pacman &> /dev/null; then
        sudo pacman -S --noconfirm android-tools
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y android-tools
    fi
fi

# Run Python setup
cd "$(dirname "$0")"
python3 setup.py

echo ""
echo "  ========================================"
echo "  To launch APK-Lator:"
echo "    python3 __main__.py"
echo "  ========================================"
echo ""
