"""
MCP Client for Credit Risk Agent
Connects to external credit services via Model Context Protocol
"""

import asyncio
import json
import logging
import subprocess
from typing import Dict, Any, Optional
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)

class CreditMCPClient:
    """Client to connect to Credit MCP Server services"""
    
    def __init__(self, server_path: str = None):
        self.server_path = server_path or "src/mcp_servers/credit_mcp_server.py"
        self.session: Optional[ClientSession] = None
        self._connected = False
        self.server_process = None
    
    async def connect(self):
        """Connect to the MCP credit server"""
        try:
            # Start the MCP server process and connect via stdio
            server_params = stdio_client(
                command="python",
                args=[self.server_path],
                env=None
            )
            
            self.session = await server_params.__aenter__()
            await self.session.initialize()
            self._connected = True
            logger.info("Connected to Credit MCP Server")
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            self._connected = False
            # Fallback: try to use internal tools
            raise
    
    async def disconnect(self):
        """Disconnect from the MCP server"""
        if self.session:
            try:
                await self.session.__aexit__(None, None, None)
                self._connected = False
                logger.info("Disconnected from Credit MCP Server")
            except Exception as e:
                logger.error(f"Error disconnecting from MCP server: {e}")
    
    async def get_credit_score(self, applicant_name: str) -> Dict[str, Any]:
        """Get credit score via MCP server"""
        if not self._connected:
            await self.connect()
        
        try:
            result = await self.session.call_tool(
                "get_credit_score",
                {"applicant_name": applicant_name}
            )
            
            # Parse the response
            if result.content and len(result.content) > 0:
                content = result.content[0]
                if hasattr(content, 'text'):
                    return json.loads(content.text)
            
            return {"error": "No response from MCP server"}
            
        except Exception as e:
            logger.error(f"MCP credit score call failed: {e}")
            return {"error": f"MCP call failed: {str(e)}"}
    
    async def predict_default_risk(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict default risk via MCP server"""
        if not self._connected:
            await self.connect()
        
        try:
            result = await self.session.call_tool(
                "predict_default_risk",
                {"financial_data": financial_data}
            )
            
            # Parse the response
            if result.content and len(result.content) > 0:
                content = result.content[0]
                if hasattr(content, 'text'):
                    return json.loads(content.text)
            
            return {"error": "No response from MCP server"}
            
        except Exception as e:
            logger.error(f"MCP risk prediction call failed: {e}")
            return {"error": f"MCP call failed: {str(e)}"}
    
    async def comprehensive_assessment(self, applicant_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive credit assessment via MCP server"""
        if not self._connected:
            await self.connect()
        
        try:
            result = await self.session.call_tool(
                "comprehensive_credit_assessment",
                {"applicant_data": applicant_data}
            )
            
            # Parse the response
            if result.content and len(result.content) > 0:
                content = result.content[0]
                if hasattr(content, 'text'):
                    return json.loads(content.text)
            
            return {"error": "No response from MCP server"}
            
        except Exception as e:
            logger.error(f"MCP comprehensive assessment call failed: {e}")
            return {"error": f"MCP call failed: {str(e)}"}
    
    async def list_available_tools(self) -> list:
        """List tools available on the MCP server"""
        if not self._connected:
            await self.connect()
        
        try:
            tools = await self.session.list_tools()
            return [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "schema": tool.inputSchema
                }
                for tool in tools.tools
            ]
        except Exception as e:
            logger.error(f"Failed to list MCP tools: {e}")
            return []
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()


# Convenience functions for easy integration
async def get_credit_score_via_mcp(applicant_name: str) -> Dict[str, Any]:
    """Convenience function to get credit score via MCP"""
    async with CreditMCPClient() as client:
        return await client.get_credit_score(applicant_name)

async def predict_risk_via_mcp(financial_data: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function to predict risk via MCP"""
    async with CreditMCPClient() as client:
        return await client.predict_default_risk(financial_data)

async def comprehensive_assessment_via_mcp(applicant_data: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function for comprehensive assessment via MCP"""
    async with CreditMCPClient() as client:
        return await client.comprehensive_assessment(applicant_data)
