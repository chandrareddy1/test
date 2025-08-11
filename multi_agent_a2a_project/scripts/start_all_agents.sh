#!/bin/bash

# Start All Agents Script (UV Version)
# This script starts all the mortgage processing agents in the background using UV

echo "🤖 Starting All Mortgage Processing Agents (UV)"
echo "==============================================="

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

# Create logs directory
mkdir -p logs

# Function to start an agent
start_agent() {
    local agent_name=$1
    local agent_path=$2
    local port=$3
    
    # Convert agent name to lowercase for file names
    local agent_file_name=$(echo "$agent_name" | tr '[:upper:]' '[:lower:]' | tr ' ' '_')
    
    # Get absolute path to project root for logs
    local project_root=$(pwd)
    
    echo "🚀 Starting $agent_name..."
    
    # Run as module from project root to handle relative imports
    nohup uv run python -m src.agents.$(basename "$agent_path") > "${project_root}/logs/${agent_file_name}.log" 2>&1 &
    agent_pid=$!
    
    echo "$agent_pid" > "${project_root}/logs/${agent_file_name}.pid"
    
    # Wait a moment and check if the agent started successfully
    sleep 2
    
    if kill -0 $agent_pid 2>/dev/null; then
        echo "✅ $agent_name started successfully (PID: $agent_pid)"
        
        # Check if port is responding (give it time to start)
        for i in {1..10}; do
            if nc -z localhost $port 2>/dev/null; then
                echo "✅ $agent_name is responding on port $port"
                break
            fi
            sleep 1
        done
    else
        echo "❌ Failed to start $agent_name"
    fi
}

# Start all agents
start_agent "Document Agent" "src/agents/document_agent" 10001
start_agent "Credit Risk Agent" "src/agents/credit_risk_agent" 10002
start_agent "Compliance Agent" "src/agents/compliance_agent" 10003
start_agent "Routing Agent" "src/agents/routing_agent" 10004

echo ""
echo "🎉 All agents started!"
echo ""
echo "📊 Agent Status:"
echo "  • Document Agent:    http://localhost:10001"
echo "  • Credit Risk Agent: http://localhost:10002"
echo "  • Compliance Agent:  http://localhost:10003"
echo "  • Routing Agent:     http://localhost:10004"
echo ""
echo "📁 Logs are available in the 'logs' directory"
echo ""
echo "💡 UV Commands:"
echo "  uv run streamlit run streamlit_mortgage_app.py  # Start Streamlit frontend"
echo "  uv run python run_mortgage_flow.py --help       # CLI mortgage processor"
echo ""
echo "🛑 To stop all agents:"
echo "  ./stop_all_agents.sh"
