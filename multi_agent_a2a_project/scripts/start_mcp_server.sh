#!/bin/bash

# Start MCP Server Script
# This script starts the Credit MCP Server for Model Context Protocol integration

echo "🔌 Starting Credit MCP Server"
echo "============================="

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

# Create logs directory if it doesn't exist
mkdir -p logs

# Check if MCP server is already running
if [ -f "logs/mcp_server.pid" ]; then
    pid=$(cat "logs/mcp_server.pid")
    if kill -0 $pid 2>/dev/null; then
        echo "⚠️  MCP Server is already running (PID: $pid)"
        echo "   Use ./scripts/stop_mcp_server.sh to stop it first"
        exit 1
    else
        # Remove stale PID file
        rm -f "logs/mcp_server.pid"
    fi
fi

echo "🚀 Starting Credit MCP Server..."

# Get absolute path to project root for logs
project_root=$(pwd)

# Start MCP server as background process
nohup uv run python utilities/mcp/servers/credit_mcp_server.py > "${project_root}/logs/mcp_server.log" 2>&1 &
mcp_pid=$!

# Save PID for later management
echo "$mcp_pid" > "${project_root}/logs/mcp_server.pid"

# Wait a moment and check if the server started successfully
sleep 3

if kill -0 $mcp_pid 2>/dev/null; then
    echo "✅ Credit MCP Server started successfully (PID: $mcp_pid)"
    echo "📋 Available tools:"
    echo "   • get_credit_score"
    echo "   • predict_default_risk"
    echo "   • comprehensive_credit_assessment"
    echo ""
    echo "📁 Logs: logs/mcp_server.log"
    echo "🔍 Monitor: tail -f logs/mcp_server.log"
else
    echo "❌ Failed to start MCP Server"
    echo "📁 Check logs: cat logs/mcp_server.log"
    rm -f "${project_root}/logs/mcp_server.pid"
    exit 1
fi

echo ""
echo "🎉 MCP Server startup complete!"
