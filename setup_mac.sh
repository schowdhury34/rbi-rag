#!/bin/bash
# setup_mac.sh — one-time setup for macOS
# Run with: bash setup_mac.sh

echo "Setting up RBI RAG on macOS..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Python3 not found. Install from https://www.python.org/downloads/"
    exit 1
fi
echo "Python: $(python3 --version)"

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip -q
pip install -r requirements.txt -q

# Create .env if not exists
if [ ! -f .env ]; then
    cp .env.example .env
    echo ".env created — add your GROQ_API_KEY inside"
fi

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Add your GROQ_API_KEY to .env"
echo "  2. source .venv/bin/activate"
echo "  3. python run.py"
