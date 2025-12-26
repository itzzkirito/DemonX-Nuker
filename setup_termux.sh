#!/data/data/com.termux/files/usr/bin/bash

# DemonX Termux Setup Script
# This script helps set up DemonX Nuker on Termux (Android)

set -e  # Exit on error

echo "=========================================="
echo "DemonX Nuker - Termux Setup"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running on Termux
if [ ! -d "/data/data/com.termux/files/usr" ]; then
    echo -e "${RED}Error: This script is designed for Termux only!${NC}"
    exit 1
fi

echo -e "${GREEN}[*]${NC} Updating Termux packages..."
pkg update -y && pkg upgrade -y

echo -e "${GREEN}[*]${NC} Installing required packages..."
pkg install -y python python-pip git

echo -e "${GREEN}[*]${NC} Upgrading pip..."
pip install --upgrade pip

echo -e "${GREEN}[*]${NC} Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo -e "${YELLOW}[!]${NC} requirements.txt not found, installing core dependencies..."
    pip install discord.py httpx colorama aiohttp rich pyfiglet
fi

echo -e "${GREEN}[*]${NC} Checking for config.json..."
if [ ! -f "config.json" ]; then
    echo -e "${YELLOW}[!]${NC} Creating default config.json..."
    cat > config.json << 'EOF'
{
  "proxy": false,
  "dry_run": false,
  "verbose": true,
  "version": "2.3"
}
EOF
    echo -e "${GREEN}[+]${NC} config.json created!"
else
    echo -e "${GREEN}[+]${NC} config.json already exists"
fi

echo -e "${GREEN}[*]${NC} Verifying Python installation..."
python3 --version

echo -e "${GREEN}[*]${NC} Checking critical dependencies..."
python3 -c "import discord; import aiohttp; import colorama; print('All dependencies OK')" 2>/dev/null || {
    echo -e "${RED}[!]${NC} Some dependencies failed to import. Trying to reinstall..."
    pip install --force-reinstall discord.py aiohttp colorama
}

echo ""
echo -e "${GREEN}=========================================="
echo -e "Setup Complete!${NC}"
echo -e "${GREEN}=========================================="
echo ""
echo "To run DemonX Nuker, use:"
echo -e "${YELLOW}  python3 demonx_complete.py${NC}"
echo ""
echo -e "${YELLOW}Note:${NC} The GUI version (demonx_gui.py) will NOT work on Termux."
echo -e "      Use the CLI version (demonx_complete.py) instead."
echo ""
echo "For background execution, use tmux:"
echo -e "${YELLOW}  pkg install tmux${NC}"
echo -e "${YELLOW}  tmux${NC}"
echo -e "${YELLOW}  python3 demonx_complete.py${NC}"
echo -e "${YELLOW}  # Detach: Ctrl+B, then D${NC}"
echo ""

