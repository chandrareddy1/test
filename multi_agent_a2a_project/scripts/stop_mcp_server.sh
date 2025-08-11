#!/bin/bash

# Stop MCP Server Script
# This script stops the running Credit MCP Server

echo "🛑 Stopping Credit MCP Server"
echo "============================="

# Check if PID file exists
if [ ! -f "logs/mcp_server.pid" ]; then
    echo "⚠️  No MCP Server PID file found"
    echo "   MCP Server may not be running or was started manually"
    
    # Try to find and kill any running MCP processes
    mcp_pids=$(pgrep -f "credit_mcp_server.py")
    if [ -n "$mcp_pids" ]; then
        echo "🔍 Found running MCP processes: $mcp_pids"
        echo "🛑 Stopping them..."
        pkill -f "credit_mcp_server.py"
        sleep 2
        echo "✅ MCP Server processes stopped"
    else
        echo "ℹ️  No running MCP Server processes found"
    fi
    exit 0
fi

# Read PID from file
mcp_pid=$(cat "logs/mcp_server.pid")

if kill -0 $mcp_pid 2>/dev/null; then
    echo "🛑 Stopping Credit MCP Server (PID: $mcp_pid)..."
    kill $mcp_pid
    
    # Wait for process to stop gracefully
    for i in {1..10}; do
        if ! kill -0 $mcp_pid 2>/dev/null; then
            echo "✅ MCP Server stopped gracefully"
            break
        fi
        sleep 1
        echo "⏳ Waiting for graceful shutdown... ($i/10)"
    done
    
    # Force kill if still running
    if kill -0 $mcp_pid 2>/dev/null; then
        echo "⚠️  Force killing MCP Server..."
        kill -9 $mcp_pid
        sleep 1
        if kill -0 $mcp_pid 2>/dev/null; then
            echo "❌ Failed to stop MCP Server"
            exit 1
        else
            echo "✅ MCP Server force stopped"
        fi
    fi
else
    echo "⚠️  MCP Server (PID: $mcp_pid) was not running"
fi

# Clean up PID file
rm -f "logs/mcp_server.pid"

echo "🎉 MCP Server stop complete!"
