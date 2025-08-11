#!/bin/bash

# Stop All Agents Script
# This script stops all the mortgage processing agents

echo "🛑 Stopping All Mortgage Processing Agents"
echo "==========================================="

# Function to stop an agent
stop_agent() {
    local agent_name=$1
    # Convert agent name to lowercase for file names  
    local agent_file_name=$(echo "$agent_name" | tr '[:upper:]' '[:lower:]' | tr ' ' '_')
    local pid_file="logs/${agent_file_name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        
        if kill -0 $pid 2>/dev/null; then
            echo "🛑 Stopping $agent_name (PID: $pid)..."
            kill $pid
            
            # Wait for process to stop
            for i in {1..5}; do
                if ! kill -0 $pid 2>/dev/null; then
                    echo "✅ $agent_name stopped"
                    break
                fi
                sleep 1
            done
            
            # Force kill if still running
            if kill -0 $pid 2>/dev/null; then
                echo "⚠️  Force killing $agent_name..."
                kill -9 $pid
                echo "✅ $agent_name force stopped"
            fi
        else
            echo "⚠️  $agent_name was not running"
        fi
        
        # Remove PID file
        rm -f "$pid_file"
    else
        echo "⚠️  No PID file found for $agent_name"
    fi
}

# Stop all agents
stop_agent "Document Agent"
stop_agent "Credit Risk Agent"
stop_agent "Compliance Agent"  
stop_agent "Routing Agent"

echo ""
echo "🎉 All agents stopped!"
echo ""

# Also kill any remaining Python processes on the agent ports
echo "🔍 Checking for remaining processes on agent ports..."

for port in 10001 10002 10003 10004; do
    pid=$(lsof -ti:$port 2>/dev/null)
    if [ -n "$pid" ]; then
        echo "🛑 Killing process on port $port (PID: $pid)"
        kill -9 $pid 2>/dev/null
    fi
done

echo "✅ Cleanup complete!"
