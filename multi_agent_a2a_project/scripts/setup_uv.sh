#!/bin/bash

# UV Setup Script for Mortgage Application Processor
# This script sets up the project using UV package manager

echo "🚀 Setting up Mortgage Application Processor with UV"
echo "=================================================="

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo "❌ UV is not installed. Installing UV..."
    
    # Install UV using the official installer
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Add UV to PATH for current session
    export PATH="$HOME/.cargo/bin:$PATH"
    
    # Check if installation was successful
    if command -v uv &> /dev/null; then
        echo "✅ UV installed successfully"
    else
        echo "❌ Failed to install UV. Please install manually:"
        echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
else
    echo "✅ UV is already installed"
fi

echo ""
echo "📦 Setting up project environment..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "🏗️  Creating virtual environment..."
    uv venv
else
    echo "✅ Virtual environment already exists"
fi

echo ""
echo "📥 Installing dependencies..."

# Install all dependencies
uv pip install -e .

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📋 Available commands:"
echo "   uv run streamlit run streamlit_mortgage_app.py  # Start Streamlit app"
echo "   uv run python run_mortgage_flow.py --help       # CLI mortgage processor"
echo "   ./start_all_agents.sh                           # Start backend agents"
echo ""
echo "💡 To activate the virtual environment manually:"
echo "   source .venv/bin/activate"
echo ""
echo "🔧 Optional dependency groups:"
echo "   uv pip install -e .[dev]        # Install development dependencies"
echo "   uv pip install -e .[streamlit]  # Install only Streamlit dependencies"
