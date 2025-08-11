#!/bin/bash

# Master Management Script for Mortgage Application Processor
# This script provides a unified interface to manage all components

echo "� MortgageInsight Pro - Management Console"
echo "=========================================="

# Change to the project root directory (one level up from scripts)
cd "$(dirname "$0")/.."

show_usage() {
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  setup              - Set up the project environment using UV"
    echo "  start-agents       - Start all mortgage processing agents"
    echo "  stop-agents        - Stop all mortgage processing agents"
    echo "  start-mcp          - Start the Credit MCP Server"
    echo "  stop-mcp           - Stop the Credit MCP Server"
    echo "  restart-mcp        - Restart the Credit MCP Server"
    echo "  start-streamlit    - Start the Streamlit web interface"
    echo "  stop-streamlit     - Stop the Streamlit web interface"
    echo "  restart-streamlit  - Restart the Streamlit web interface"
    echo "  start-all          - Start agents, MCP server, and Streamlit (full system)"
    echo "  stop-all           - Stop everything (agents, MCP server, and Streamlit)"
    echo "  restart-all        - Restart everything (agents, MCP server, and Streamlit)"
    echo "  status             - Check status of all components"
    echo "  help               - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 setup"
    echo "  $0 start-all"
    echo "  $0 start-mcp"
    echo "  $0 restart-streamlit"
    echo "  $0 status"
    echo ""
}

check_status() {
    echo "🔍 Checking system status..."
    echo ""
    
    # Check UV installation
    if command -v uv &> /dev/null; then
        echo "✅ UV package manager: Installed"
    else
        echo "❌ UV package manager: Not installed"
    fi
    
    # Check virtual environment
    if [ -d ".venv" ]; then
        echo "✅ Virtual environment: Exists"
    else
        echo "❌ Virtual environment: Not found"
    fi
    
    echo ""
    echo "🤖 Agent Status:"
    
    # Check agent ports
    agents=(
        "10001:Document Agent"
        "10002:Credit Risk Agent"
        "10003:Compliance Agent"
        "10004:Routing Agent"
    )
    
    for agent in "${agents[@]}"; do
        port=$(echo $agent | cut -d: -f1)
        name=$(echo $agent | cut -d: -f2)
        
        if nc -z localhost $port 2>/dev/null; then
            echo "✅ $name (port $port): Running"
        else
            echo "❌ $name (port $port): Not running"
        fi
    done
    
    echo ""
    echo "🔌 MCP Server Status:"
    
    # Check MCP Server
    if [ -f "logs/mcp_server.pid" ]; then
        mcp_pid=$(cat "logs/mcp_server.pid")
        if kill -0 $mcp_pid 2>/dev/null; then
            echo "✅ Credit MCP Server (PID: $mcp_pid): Running"
            echo "   📋 Tools: get_credit_score, predict_default_risk, comprehensive_credit_assessment"
        else
            echo "❌ Credit MCP Server: PID file exists but process not running"
        fi
    else
        echo "❌ Credit MCP Server: Not running"
    fi
    
    echo ""
    echo "🌐 MortgageInsight Pro Status:"
    
    # Check Streamlit
    if pgrep -f "streamlit run frontend/mortgage_analyzer_app.py" > /dev/null; then
        streamlit_port=$(lsof -i :8501 2>/dev/null | grep LISTEN | awk '{print $9}' | cut -d: -f2)
        if [ -n "$streamlit_port" ]; then
            echo "✅ MortgageInsight Pro Frontend (port $streamlit_port): Running"
            echo "   🌐 Access at: http://localhost:$streamlit_port"
        else
            echo "✅ MortgageInsight Pro Frontend: Running (port unknown)"
        fi
    else
        echo "❌ MortgageInsight Pro Frontend: Not running"
    fi
    
    echo ""
}

case "$1" in
    setup)
        echo "🚀 Setting up project..."
        ./scripts/setup_uv.sh
        ;;
    start-agents)
        echo "🤖 Starting all agents..."
        ./scripts/start_all_agents.sh
        ;;
    stop-agents)
        echo "🛑 Stopping all agents..."
        ./scripts/stop_all_agents.sh
        ;;
    start-mcp)
        echo "🔌 Starting MCP Server..."
        ./scripts/start_mcp_server.sh
        ;;
    stop-mcp)
        echo "🛑 Stopping MCP Server..."
        ./scripts/stop_mcp_server.sh
        ;;
    restart-mcp)
        echo "🔄 Restarting MCP Server..."
        ./scripts/restart_mcp_server.sh
        ;;
    start-streamlit)
        echo "🌐 Starting Streamlit..."
        ./scripts/start_streamlit_app.sh
        ;;
    stop-streamlit)
        echo "🛑 Stopping Streamlit..."
        ./scripts/stop_streamlit.sh
        ;;
    restart-streamlit)
        echo "🔄 Restarting Streamlit..."
        ./scripts/restart_streamlit.sh
        ;;
    start-all)
        echo "🚀 Starting full system..."
        ./scripts/start_all_agents.sh
        sleep 3
        ./scripts/start_mcp_server.sh
        sleep 2
        ./scripts/start_streamlit_app.sh
        ;;
    stop-all)
        echo "🛑 Stopping full system..."
        ./scripts/stop_streamlit.sh
        ./scripts/stop_mcp_server.sh
        ./scripts/stop_all_agents.sh
        ;;
    restart-all)
        echo "🔄 Restarting full system..."
        ./scripts/stop_streamlit.sh
        ./scripts/stop_mcp_server.sh
        ./scripts/stop_all_agents.sh
        sleep 3
        ./scripts/start_all_agents.sh
        sleep 3
        ./scripts/start_mcp_server.sh
        sleep 2
        ./scripts/start_streamlit_app.sh
        ;;
    status)
        check_status
        ;;
    help|--help|-h)
        show_usage
        ;;
    "")
        echo "❌ No command specified."
        show_usage
        exit 1
        ;;
    *)
        echo "❌ Unknown command: $1"
        show_usage
        exit 1
        ;;
esac
