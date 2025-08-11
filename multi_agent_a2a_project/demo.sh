#!/bin/bash

# MortgageInsight Pro - Quick Start Demo
# This script demonstrates the reorganized project structure and launches the application

echo "🏦 MortgageInsight Pro - Quick Start Demo"
echo "========================================"
echo ""

echo "📁 Project Structure Overview:"
echo "├── scripts/          - All management scripts"
echo "├── frontend/         - MortgageInsight Pro web app"
echo "├── src/agents/       - Multi-agent AI system"
echo "├── utilities/        - A2A protocol & tools"
echo "└── mortgage_docs/    - Sample documents"
echo ""

echo "🎯 Available Commands:"
echo "   ./scripts/manage.sh setup              - Initial setup"
echo "   ./scripts/manage.sh start-all          - Start complete system (agents + MCP + web)"
echo "   ./scripts/manage.sh start-mcp          - Start MCP server only"
echo "   ./scripts/manage.sh status             - Check system status"
echo "   ./scripts/manage.sh restart-streamlit  - Restart web interface"
echo "   ./scripts/manage.sh stop-all           - Stop everything"
echo ""

echo "🚀 Quick Demo Launch:"
echo "1. Setting up the system..."

# Check if UV is available
if ! command -v uv &> /dev/null; then
    echo "⚠️  UV not found. Running setup..."
    ./scripts/manage.sh setup
else
    echo "✅ UV package manager ready"
fi

echo ""
echo "2. Starting the complete system (agents + MCP server + web interface)..."
./scripts/manage.sh start-all

echo ""
echo "🎉 Demo Complete!"
echo ""
echo "📱 Access MortgageInsight Pro at: http://localhost:8501"
echo "🤖 All agents are running in the background"
echo "🔌 MCP Server provides credit tools and risk assessment"
echo "📄 Upload a PDF from mortgage_docs/input/ to test"
echo ""
echo "💡 Management Commands:"
echo "   - Check status: ./scripts/manage.sh status"
echo "   - Stop system: ./scripts/manage.sh stop-all" 
echo "   - Restart app: ./scripts/manage.sh restart-streamlit"
echo "   - Restart MCP: ./scripts/manage.sh restart-mcp"
echo "   - Monitor logs: ./scripts/monitor_logs.sh"
echo ""
