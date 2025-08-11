#!/usr/bin/env python3
"""
MCP Server Manager
==================

Helper script to manage MCP servers for the mortgage processing system.
"""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))


def load_mcp_config():
    """Load MCP configuration from config file"""
    config_path = Path(__file__).parent / "mcp_config.json"
    with open(config_path, 'r') as f:
        return json.load(f)


def start_credit_server():
    """Start the Credit MCP Server"""
    print("🚀 Starting Credit MCP Server...")
    config = load_mcp_config()
    server_config = config["mcp_servers"]["credit_server"]
    
    script_path = project_root / server_config["location"]
    cmd = ["python", str(script_path)]
    
    print(f"Command: {' '.join(cmd)}")
    print(f"Working directory: {project_root}")
    
    try:
        # Run the server
        subprocess.run(cmd, cwd=project_root)
    except KeyboardInterrupt:
        print("\n⏹️  Credit MCP Server stopped")
    except Exception as e:
        print(f"❌ Failed to start Credit MCP Server: {e}")


def list_servers():
    """List available MCP servers"""
    config = load_mcp_config()
    print("📋 Available MCP Servers:")
    print("=" * 40)
    
    for server_id, server_config in config["mcp_servers"].items():
        print(f"🔧 {server_config['name']} ({server_id})")
        print(f"   Description: {server_config['description']}")
        print(f"   Location: {server_config['location']}")
        print(f"   Tools: {', '.join(server_config['tools'])}")
        print()


def main():
    """Main CLI interface"""
    if len(sys.argv) < 2:
        print("Usage: python mcp_manager.py <command>")
        print()
        print("Commands:")
        print("  start-credit    Start the Credit MCP Server")
        print("  list           List available MCP servers")
        return
    
    command = sys.argv[1]
    
    if command == "start-credit":
        start_credit_server()
    elif command == "list":
        list_servers()
    else:
        print(f"Unknown command: {command}")
        print("Use 'list' to see available commands")


if __name__ == "__main__":
    main()
