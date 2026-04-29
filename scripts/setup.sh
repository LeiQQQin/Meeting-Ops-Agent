#!/usr/bin/env bash
# Meeting-Ops-Agent local setup script
set -e

echo "🤖 Meeting-Ops-Agent Setup"
echo "=========================="

# Check prerequisites
command -v python3 >/dev/null 2>&1 || { echo "Python 3 is required"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "Node.js is required"; exit 1; }

# Copy env if needed
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env from .env.example"
    echo "⚠️  Please edit .env and add your OPENAI_API_KEY before continuing"
fi

# Backend setup
echo ""
echo "📦 Setting up Python backend..."
cd src/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✅ Backend dependencies installed"
cd ../..

# Frontend setup
echo ""
echo "📦 Setting up frontend..."
cd src/frontend
npm install --silent
echo "✅ Frontend dependencies installed"
cd ../..

# Create upload directory
mkdir -p uploads data

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the development servers, run:"
echo "  ./scripts/run_local.sh"
