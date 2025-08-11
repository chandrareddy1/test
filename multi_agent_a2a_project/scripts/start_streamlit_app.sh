#!/bin/bash

# Streamlit Mortgage App Startup Script (UV Version)
# This script starts the Streamlit frontend for the mortgage application processor

echo "� Starting MortgageInsight Pro - AI Analysis Platform (UV)"
echo "========================================================"

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo "❌ UV is not installed. Please run ./setup_uv.sh first"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run ./setup_uv.sh first"
    exit 1
fi

echo "🔍 Checking if agents are running..."

# Function to check if a service is running on a port
check_port() {
    local port=$1
    local service=$2
    
    if nc -z localhost $port 2>/dev/null; then
        echo "✅ $service is running on port $port"
        return 0
    else
        echo "❌ $service is NOT running on port $port"
        return 1
    fi
}

# Check all required agents
agents_running=true

if ! check_port 10001 "Document Agent"; then
    agents_running=false
fi

if ! check_port 10002 "Credit Risk Agent"; then
    agents_running=false
fi

if ! check_port 10003 "Compliance Agent"; then
    agents_running=false
fi

if ! check_port 10004 "Routing Agent"; then
    agents_running=false
fi

if [ "$agents_running" = false ]; then
    echo ""
    echo "⚠️  Some agents are not running. Please start them first:"
    echo ""
    echo "# Start all agents:"
    echo "./start_all_agents.sh"
    echo ""
    echo "# Or start individual agents with UV:"
    echo "uv run python src/agents/document_agent/__main__.py &"
    echo "uv run python src/agents/credit_risk_agent/__main__.py &"
    echo "uv run python src/agents/compliance_agent/__main__.py &"
    echo "uv run python src/agents/routing_agent/__main__.py &"
    echo ""
    read -p "Do you want to continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting..."
        exit 1
    fi
else
    echo "✅ All agents are running!"
fi

echo ""
echo "🚀 Starting MortgageInsight Pro frontend with UV..."
echo "📱 The app will open in your browser at: http://localhost:8501"
echo ""

# Start Streamlit app using UV
uv run streamlit run frontend/mortgage_analyzer_app.py \
    --server.port 8501 \
    --server.address localhost \
    --server.headless false \
    --browser.gatherUsageStats false \
    --theme.base light \
    --theme.primaryColor "#1f4e79" \
    --theme.backgroundColor "#ffffff" \
    --theme.secondaryBackgroundColor "#f0f2f6"
