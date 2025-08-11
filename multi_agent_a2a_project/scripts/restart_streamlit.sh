#!/bin/bash

# Restart Streamlit App Script
# This script stops any running Streamlit processes and starts a fresh instance

echo "🔄 Restarting MortgageInsight Pro - AI Analysis Platform"
echo "===================================================="

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo "❌ UV is not installed. Please run ./setup_uv.sh first"
    exit 1
fi

# Stop any running Streamlit processes
echo "🛑 Stopping existing Streamlit processes..."
pkill -f "streamlit run frontend/mortgage_analyzer_app.py" 2>/dev/null && echo "✅ Stopped existing Streamlit processes" || echo "ℹ️  No existing Streamlit processes found"

# Wait a moment for processes to fully stop
sleep 2

# Check if agents are running
echo ""
echo "🔍 Checking if agents are running..."

agents_running=true
for port in 10001 10002 10003 10004; do
    if nc -z localhost $port 2>/dev/null; then
        echo "✅ Agent on port $port is running"
    else
        echo "❌ Agent on port $port is NOT running"
        agents_running=false
    fi
done

if [ "$agents_running" = false ]; then
    echo ""
    echo "⚠️  Some agents are not running. You may want to start them first:"
    echo "./start_all_agents.sh"
    echo ""
fi

# Start Streamlit
echo "🚀 Starting fresh Streamlit instance..."
echo "📱 Opening at: http://localhost:8501"
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
