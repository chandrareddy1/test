# MCP (Model Context Protocol) Utilities

This directory contains all MCP-related components for the mortgage processing system.

## 📁 Structure

```
utilities/mcp/
├── __init__.py                 # Main MCP utilities package
├── mcp_config.json            # MCP configuration
├── mcp_discovery.py           # MCP discovery utilities  
├── mcp_manager.py             # MCP server management
├── clients/                   # MCP client implementations
│   ├── __init__.py
│   └── mcp_client.py         # Credit MCP client
├── servers/                   # MCP server implementations
│   ├── __init__.py
│   └── credit_mcp_server.py  # Credit services server
└── tools/                     # MCP tools and integrations
    ├── __init__.py
    └── mcp_credit_tools.py   # Credit risk assessment tools
```

## 🚀 Quick Start

### List Available MCP Components
```bash
python utilities/mcp/mcp_discovery.py
```

### Start Credit MCP Server
```bash
python utilities/mcp/mcp_manager.py start-credit
```

### List All MCP Servers
```bash
python utilities/mcp/mcp_manager.py list
```

## 🔧 Components

### Servers
- **Credit MCP Server**: Provides credit scoring and risk assessment services
  - Tools: `get_credit_score`, `predict_default_risk`, `comprehensive_credit_assessment`
  - Transport: stdio
  - Location: `utilities/mcp/servers/credit_mcp_server.py`

### Clients  
- **Credit MCP Client**: Client for connecting to credit MCP servers
  - Supports stdio transport
  - Location: `utilities/mcp/clients/mcp_client.py`

### Tools
- **MockCreditAPITool**: Simulated credit API for testing
- **VertexAIRiskTool**: AI-powered risk assessment
- **MCPCreditBroker**: MCP service broker for credit operations

## 📖 Usage in Agents

### Import MCP Components
```python
from utilities.mcp.clients.mcp_client import CreditMCPClient
from utilities.mcp.tools.mcp_credit_tools import MockCreditAPITool, MCPCreditBroker
```

### Using in Credit Risk Agent
```python
class CreditRiskAgent:
    def __init__(self):
        self.mcp_client = CreditMCPClient()
        self.mcp_broker = MCPCreditBroker()
        self.credit_api_tool = MockCreditAPITool()
```

## ⚙️ Configuration

The `mcp_config.json` file contains all MCP component configurations:

- **mcp_servers**: Server definitions and startup commands
- **mcp_clients**: Client configurations and connection details  
- **mcp_tools**: Tool definitions and locations

## 🔄 Integration with A2A

The MCP utilities are designed to work seamlessly with the A2A (Agent-to-Agent) framework:

1. **Document Agent** processes PDFs and extracts data
2. **Credit Risk Agent** uses MCP tools for enhanced credit analysis
3. **MCP Credit Server** provides specialized credit services
4. **A2A Protocol** enables agent communication

## 🛠️ Development

### Adding New MCP Tools
1. Create tool class in `utilities/mcp/tools/`
2. Update `utilities/mcp/tools/__init__.py` 
3. Add configuration to `mcp_config.json`
4. Import in your agent

### Adding New MCP Servers
1. Create server in `utilities/mcp/servers/`
2. Add FastMCP tools and endpoints
3. Update `mcp_config.json`
4. Add startup command to `mcp_manager.py`

## 📋 Testing

Test the MCP utilities:
```bash
# Test imports (within virtual environment)
source .venv/bin/activate && python -c "from utilities.mcp.tools.mcp_credit_tools import MockCreditAPITool; print('✅ MCP tools working')"

# Test discovery
python utilities/mcp/mcp_discovery.py

# Test Credit Risk Agent with organized structure
python tests/agents/test_credit_agent.py
```

## 🎯 Benefits

- **Organized Structure**: Clear separation of clients, servers, and tools
- **Easy Management**: Centralized configuration and management scripts
- **Reusable Components**: MCP tools can be used across multiple agents
- **Production Ready**: Proper package structure for deployment
- **Maintainable**: Clear organization makes updates and debugging easier

This MCP utilities package provides a robust foundation for extending the mortgage processing system with additional AI-powered credit services! 🏦✨
