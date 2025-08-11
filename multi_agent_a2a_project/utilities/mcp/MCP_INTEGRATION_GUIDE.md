# MCP Credit Services Integration Guide

## Overview

The Credit Risk Agent now supports **Model Context Protocol (MCP)** integration, allowing credit risk assessment services to be exposed as external MCP servers that other agents can connect to.

## Architecture

```
┌─────────────────┐    MCP Protocol    ┌─────────────────┐
│   Client Agent  │ ◄─────────────────► │  Credit MCP     │
│  (Credit Risk)  │    (stdio/JSON)    │     Server      │
└─────────────────┘                    └─────────────────┘
                                                │
                                                ▼
                                       ┌─────────────────┐
                                       │  Credit Tools   │
                                       │ • MockCreditAPI │
                                       │ • VertexAI Risk │
                                       │ • Comprehensive │
                                       └─────────────────┘
```

## Components

### 1. MCP Server (`utilities/mcp/servers/credit_mcp_server.py`)

**Purpose**: Exposes credit services via Model Context Protocol

**Available Tools**:
- `get_credit_score` - Credit bureau API simulation
- `predict_default_risk` - AI-powered risk assessment
- `comprehensive_credit_assessment` - Full credit evaluation

**Usage**:
```bash
python utilities/mcp/servers/credit_mcp_server.py
```

### 2. MCP Client (`utilities/mcp/clients/mcp_client.py`)

**Purpose**: Connects to external MCP credit services

**Methods**:
- `get_credit_score(applicant_name)` - Get credit data
- `predict_default_risk(financial_data)` - Risk assessment
- `comprehensive_assessment(applicant_data)` - Full evaluation

**Usage**:
```python
async with CreditMCPClient() as client:
    result = await client.get_credit_score("John Doe")
```

### 3. Enhanced Credit Risk Agent

**Features**:
- ✅ MCP server connectivity with fallback to internal tools
- ✅ Automatic DTI > 43% risk flagging
- ✅ A2A messaging integration
- ✅ Comprehensive risk assessment

## Quick Start

### 1. Start MCP Server
```bash
cd /path/to/project
python utilities/mcp/servers/credit_mcp_server.py
```

### 2. Test MCP Integration
```bash
python tests/integration/test_complete_a2a_mcp.py
```

### 3. Test Individual MCP Tools
```bash
python tests/mcp/test_mcp_tools.py
```

## MCP Tool Specifications

### get_credit_score
```json
{
  "name": "get_credit_score",
  "description": "Get credit score and history from credit bureau API",
  "input": {
    "applicant_name": "string"
  },
  "output": {
    "credit_score": "number",
    "payment_history": "string",
    "credit_utilization": "string",
    "credit_history_length": "string"
  }
}
```

### predict_default_risk
```json
{
  "name": "predict_default_risk", 
  "description": "Use AI model to predict default risk",
  "input": {
    "financial_data": {
      "credit_score": "number",
      "dti_ratio": "number", 
      "ltv_ratio": "number",
      "annual_income": "number"
    }
  },
  "output": {
    "default_probability": "number",
    "risk_category": "string",
    "model_confidence": "number"
  }
}
```

### comprehensive_credit_assessment
```json
{
  "name": "comprehensive_credit_assessment",
  "description": "Complete credit evaluation using all services",
  "input": {
    "applicant_data": {
      "applicant_name": "string",
      "credit_score": "number (optional)",
      "dti_ratio": "number (optional)", 
      "ltv_ratio": "number (optional)",
      "annual_income": "number (optional)"
    }
  },
  "output": {
    "applicant_name": "string",
    "credit_data": "object",
    "risk_assessment": "object", 
    "financial_metrics": "object",
    "mcp_server": "string"
  }
}
```

## Integration Examples

### External Agent Connection
```python
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client

# Connect to credit MCP server
server_params = stdio_client(
    command="python",
    args=["utilities/mcp/servers/credit_mcp_server.py"]
)

async with server_params as session:
    await session.initialize()
    
    # Call credit tools
    result = await session.call_tool(
        "get_credit_score",
        {"applicant_name": "Jane Smith"}
    )
```

### A2A Agent Usage
```python
# Credit Risk Agent automatically uses MCP when available
credit_agent = CreditRiskAgent()
await credit_agent.create()

# Process document data (will use MCP server if running)
document_data = {...}  # From Document Agent
assessment = await credit_agent.process_document_data(document_data)
```

## Risk Assessment Features

### DTI Risk Flagging
- ✅ **DTI > 43%**: HIGH DTI RISK flag
- ✅ **DTI > 36%**: ELEVATED DTI warning
- ✅ **LTV > 95%**: HIGH LTV RISK flag
- ✅ **Credit < 620**: POOR CREDIT flag

### AI-Powered Assessment
- ✅ Vertex AI risk modeling simulation
- ✅ Feature importance analysis
- ✅ SHAP value generation
- ✅ Model confidence scoring

### Decision Engine
- ✅ **APPROVE**: Low risk profile
- ✅ **CONDITIONAL_APPROVAL**: Medium risk with conditions
- ✅ **DECLINE**: High risk (DTI > 43% or Credit < 620)

## Troubleshooting

### MCP Server Issues
```bash
# Check if server is running
ps aux | grep credit_mcp_server

# Test server connectivity
python tests/mcp/test_mcp_tools.py

# Check logs
tail -f /tmp/credit_mcp_server.log
```

### Client Connection Issues
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test basic connectivity
from utilities.mcp.clients.mcp_client import CreditMCPClient
async with CreditMCPClient() as client:
    tools = await client.list_available_tools()
    print(f"Available tools: {tools}")
```

### Fallback Behavior
The Credit Risk Agent will automatically fallback to internal tools if:
- MCP server is not running
- Connection fails
- Tool calls timeout
- Server returns errors

## Performance Metrics

### MCP Tool Response Times
- `get_credit_score`: ~500ms (includes API simulation delay)
- `predict_default_risk`: ~1000ms (includes ML model simulation)
- `comprehensive_credit_assessment`: ~1500ms (combines both)

### A2A Integration
- Document Agent → Credit Agent: ~2-3 seconds end-to-end
- Includes PDF processing, MCP calls, and risk assessment
- DTI calculation and risk flagging: ~50ms

## Next Steps

1. **Production MCP Server**: Replace mock APIs with real credit bureau integrations
2. **Vertex AI Integration**: Connect to actual Google Cloud Vertex AI models
3. **Monitoring**: Add MCP server health checks and metrics
4. **Security**: Implement authentication and rate limiting
5. **Scaling**: Add load balancing for multiple MCP server instances

## Related Files

- `utilities/mcp/servers/credit_mcp_server.py` - MCP server implementation
- `utilities/mcp/clients/mcp_client.py` - MCP client
- `utilities/mcp/tools/mcp_credit_tools.py` - MCP tools and utilities
- `src/agents/credit_risk_agent/agent.py` - Enhanced agent with MCP
- `tests/integration/test_complete_a2a_mcp.py` - Comprehensive A2A + MCP testing
- `tests/mcp/test_mcp_tools.py` - Individual MCP tool testing
- `utilities/mcp/README.md` - MCP utilities documentation
