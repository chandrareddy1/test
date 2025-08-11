#!/bin/bash

# Stop Streamlit App Script
# This script stops any running Streamlit processes

echo "🛑 Stopping MortgageInsight Pro - AI Analysis Platform"
echo "================================================="

# Stop any running Streamlit processes
echo "🔍 Looking for Streamlit processes..."

# Find and kill all streamlit processes
streamlit_pids=$(pgrep -f "streamlit run frontend/mortgage_analyzer_app.py")

if [ -n "$streamlit_pids" ]; then
    echo "🛑 Stopping Streamlit processes: $streamlit_pids"
    pkill -f "streamlit run frontend/mortgage_analyzer_app.py"
    
    # Wait for processes to stop
    sleep 3
    
    # Check if any are still running
    remaining_pids=$(pgrep -f "streamlit run frontend/mortgage_analyzer_app.py")
    
    if [ -n "$remaining_pids" ]; then
        echo "⚠️  Force killing remaining processes: $remaining_pids"
        pkill -9 -f "streamlit run frontend/mortgage_analyzer_app.py"
        sleep 1
    fi
    
    echo "✅ Streamlit stopped successfully"
else
    echo "ℹ️  No Streamlit processes found"
fi

echo ""
echo "🎉 Streamlit stop complete!"
