#!/bin/bash

# Exit if any command fails
set -e

echo "📦 Installing Python 3.10..."
brew install python@3.10

echo "🔗 Linking Python 3.10..."
brew link python@3.10 --force

echo "📂 Navigating to project folder..."
cd "$(dirname "$0")"

echo "🐍 Creating virtual environment (.venv)..."
python3.10 -m venv .venv

echo "✅ Activating virtual environment..."
source .venv/bin/activate

echo "⬆️ Upgrading pip..."
pip install --upgrade pip

echo "📦 Installing dependencies..."
pip install \
    "numpy<2.0" \
    torch==2.1.2 torchvision==0.16.2 \
    easyocr==1.7.1 \
    opencv-python-headless==4.8.1.78 \
    pillow==10.2.0 \
    pandas==2.1.4 \
    streamlit==1.28.0 \
    plotly==5.15.0 \
    pyttsx3==2.90 \
    gTTS==2.5.1 \
    pygame==2.5.2

echo "✅ Setup complete!"
echo "💡 In VS Code, press Cmd+Shift+P → 'Python: Select Interpreter' → choose:"
echo "$(pwd)/.venv/bin/python"
