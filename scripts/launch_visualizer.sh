#!/bin/bash

##
## EPITECH PROJECT, 2025
## Gomoku Visualizer Launcher
## File description:
## Script to install dependencies and launch the PySide6 visualizer
##

set -e  # Exit on any error

REPLAY_FILE=""
if [ $# -gt 0 ]; then
    REPLAY_FILE="$1"
    if [ ! -f "$REPLAY_FILE" ]; then
        echo "Error: Replay file '$REPLAY_FILE' not found"
        exit 1
    fi
fi

echo "🚀 Gomoku Visualizer Launcher"
echo "=============================="

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

if [ ! -f "visualizer/run_visualizer_pyside.py" ]; then
    print_error "Please run this script from the Gomoku project root directory"
    exit 1
fi

print_status "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
print_status "Python version: $python_version"

if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is not installed. Please install pip3 first."
    exit 1
fi

print_status "Checking PySide6 installation..."
if ! python3 -c "import PySide6" &> /dev/null; then
    print_warning "PySide6 not found. Installing..."
    if pip3 install PySide6; then
        print_success "PySide6 installed successfully"
    else
        print_error "Failed to install PySide6"
        exit 1
    fi
else
    pyside_version=$(python3 -c "import PySide6; print(PySide6.__version__)" 2>/dev/null)
    print_success "PySide6 $pyside_version is already installed"
fi

if [ -z "$REPLAY_FILE" ]; then
    if [ -f "replay.log" ]; then
        REPLAY_FILE="replay.log"
        print_status "Found replay.log in current directory"
    else
        print_warning "No replay.log found and no file specified"
        print_status "The visualizer will start without a replay file"
    fi
else
    print_status "Using specified replay file: $REPLAY_FILE"
fi

print_status "Launching Gomoku Visualizer..."
if [ -n "$REPLAY_FILE" ]; then
    print_status "Loading replay file: $REPLAY_FILE"
    python3 visualizer/run_visualizer_pyside.py "$REPLAY_FILE"
else
    print_status "Starting visualizer without replay file"
    python3 visualizer/run_visualizer_pyside.py
fi

print_success "Visualizer closed"
