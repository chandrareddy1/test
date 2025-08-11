#!/bin/bash

# Log Monitor Script - Real-time system monitoring
# This script provides live monitoring of all agent logs

echo "📊 MortgageInsight Pro - Live Log Monitor"
echo "========================================"
echo ""

# Check if logs directory exists
if [ ! -d "logs" ]; then
    echo "❌ Logs directory not found. Start the agents first:"
    echo "   ./scripts/manage.sh start-agents"
    exit 1
fi

# Check if any log files exist
if [ ! -f logs/*.log 2>/dev/null ]; then
    echo "❌ No log files found. Start the agents first:"
    echo "   ./scripts/manage.sh start-agents"
    exit 1
fi

echo "🔍 Available log files:"
ls -la logs/*.log 2>/dev/null | awk '{print "   📄 " $9 " (" $5 " bytes)"}'
echo ""

echo "📡 Monitoring Options:"
echo "1. All agents (combined)"
echo "2. Document Agent only"
echo "3. Credit Risk Agent only" 
echo "4. Compliance Agent only"
echo "5. Routing Agent only"
echo "6. MCP Server only"
echo "7. Error messages only"
echo "8. Recent activity (last 50 lines)"
echo ""

read -p "Select option (1-8): " choice

case $choice in
    1)
        echo "🔄 Monitoring all agents (Ctrl+C to stop)..."
        tail -f logs/*.log
        ;;
    2)
        echo "🔄 Monitoring Document Agent (Ctrl+C to stop)..."
        tail -f logs/document_agent.log
        ;;
    3)
        echo "🔄 Monitoring Credit Risk Agent (Ctrl+C to stop)..."
        tail -f logs/credit_risk_agent.log
        ;;
    4)
        echo "🔄 Monitoring Compliance Agent (Ctrl+C to stop)..."
        tail -f logs/compliance_agent.log
        ;;
    5)
        echo "🔄 Monitoring Routing Agent (Ctrl+C to stop)..."
        tail -f logs/routing_agent.log
        ;;
    6)
        echo "� Monitoring MCP Server (Ctrl+C to stop)..."
        if [ -f logs/mcp_server.log ]; then
            tail -f logs/mcp_server.log
        else
            echo "❌ MCP Server log not found. Is the MCP server running?"
            echo "   Start it with: ./scripts/start_mcp_server.sh"
        fi
        ;;
    7)
        echo "�🚨 Showing recent errors..."
        grep -i "error\|critical\|warning" logs/*.log | tail -20
        ;;
    8)
        echo "📋 Recent activity across all agents..."
        tail -50 logs/*.log
        ;;
    *)
        echo "❌ Invalid option"
        exit 1
        ;;
esac
