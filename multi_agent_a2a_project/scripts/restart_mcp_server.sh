#!/bin/bash

# Restart MCP Server Script
# This script stops and restarts the Credit MCP Server

echo "🔄 Restarting Credit MCP Server"
echo "==============================="

# Stop the MCP server
echo "🛑 Stopping existing MCP Server..."
./scripts/stop_mcp_server.sh

# Wait a moment
sleep 2

# Start the MCP server
echo ""
echo "🚀 Starting fresh MCP Server..."
./scripts/start_mcp_server.sh

echo ""
echo "🎉 MCP Server restart complete!"
