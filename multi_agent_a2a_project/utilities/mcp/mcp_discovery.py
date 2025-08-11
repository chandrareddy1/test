#!/usr/bin/env python3
"""
MCP Discovery Utility
====================

Utilities for discovering and connecting to MCP servers.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class MCPDiscovery:
    """Discover and manage MCP servers"""
    
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = Path(__file__).parent / "mcp_config.json"
        
        with open(config_path, 'r') as f:
            self.config = json.load(f)
    
    def list_servers(self) -> Dict[str, Dict]:
        """List all configured MCP servers"""
        return self.config.get("mcp_servers", {})
    
    def list_clients(self) -> Dict[str, Dict]:
        """List all configured MCP clients"""
        return self.config.get("mcp_clients", {})
    
    def list_tools(self) -> Dict[str, Dict]:
        """List all configured MCP tools"""
        return self.config.get("mcp_tools", {})
    
    def get_server_config(self, server_id: str) -> Optional[Dict]:
        """Get configuration for a specific server"""
        return self.config.get("mcp_servers", {}).get(server_id)
    
    def get_client_config(self, client_id: str) -> Optional[Dict]:
        """Get configuration for a specific client"""
        return self.config.get("mcp_clients", {}).get(client_id)
    
    def get_tools_config(self, tools_id: str) -> Optional[Dict]:
        """Get configuration for specific tools"""
        return self.config.get("mcp_tools", {}).get(tools_id)
    
    async def check_server_status(self, server_id: str) -> bool:
        """Check if a server is running (placeholder for future implementation)"""
        # This would need to be implemented based on transport type
        # For now, return True as placeholder
        return True
    
    def print_server_summary(self):
        """Print a summary of all MCP components"""
        print("🔍 MCP Components Summary")
        print("=" * 50)
        
        servers = self.list_servers()
        clients = self.list_clients()
        tools = self.list_tools()
        
        print(f"\n📡 Servers ({len(servers)}):")
        for server_id, config in servers.items():
            print(f"  • {config['name']} ({server_id})")
            print(f"    Tools: {', '.join(config['tools'])}")
        
        print(f"\n🔌 Clients ({len(clients)}):")
        for client_id, config in clients.items():
            print(f"  • {config['name']} ({client_id})")
        
        print(f"\n🛠️  Tool Sets ({len(tools)}):")
        for tools_id, config in tools.items():
            print(f"  • {config['name']} ({tools_id})")
            print(f"    Tools: {', '.join(config['tools'])}")


async def main():
    """CLI interface for MCP discovery"""
    discovery = MCPDiscovery()
    discovery.print_server_summary()


if __name__ == "__main__":
    asyncio.run(main())
