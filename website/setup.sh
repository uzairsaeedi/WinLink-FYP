#!/bin/bash

echo "========================================"
echo " WinLink Website Setup"
echo "========================================"
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "[ERROR] Node.js is not installed!"
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

echo "[OK] Node.js is installed"
node --version
npm --version
echo ""

# Navigate to website directory
cd "$(dirname "$0")"

echo "Installing dependencies..."
npm install

if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install dependencies"
    exit 1
fi

echo ""
echo "========================================"
echo " Setup Complete!"
echo "========================================"
echo ""
echo "To start the development server, run:"
echo "  npm run dev"
echo ""
echo "To build for production, run:"
echo "  npm run build"
echo ""
