# MCP Server Management Scripts

## 🔌 Credit MCP Server Integration

The Model Context Protocol (MCP) server provides credit scoring and risk assessment tools that can be used by external clients and Claude Desktop integration.

### 📁 MCP Scripts Added

```
scripts/
├── start_mcp_server.sh     # Start the Credit MCP Server
├── stop_mcp_server.sh      # Stop the Credit MCP Server
└── restart_mcp_server.sh   # Restart the Credit MCP Server
```

### 🛠️ MCP Management Commands

#### Individual Commands
```bash
# Start MCP server
./scripts/start_mcp_server.sh

# Stop MCP server  
./scripts/stop_mcp_server.sh

# Restart MCP server
./scripts/restart_mcp_server.sh
```

#### Master Control (Recommended)
```bash
# Start MCP server only
./scripts/manage.sh start-mcp

# Start everything (agents + MCP + web)
./scripts/manage.sh start-all

# Check all components including MCP
./scripts/manage.sh status

# Stop everything including MCP
./scripts/manage.sh stop-all
```

### 🔍 MCP Server Details

**Location**: `utilities/mcp/servers/credit_mcp_server.py`

**Available Tools**:
- `get_credit_score` - Retrieve credit scores for applicants
- `predict_default_risk` - Assess default probability
- `comprehensive_credit_assessment` - Full credit analysis

**Transport**: STDIO (Standard Input/Output)
**Logs**: `logs/mcp_server.log`
**PID File**: `logs/mcp_server.pid`

### 📊 Monitoring MCP Server

#### Check Status
```bash
# Overall system status (includes MCP)
./scripts/manage.sh status

# Monitor MCP logs specifically
./scripts/monitor_logs.sh
# Then select option 6 (MCP Server only)
```

#### Log Analysis
```bash
# View MCP server logs
tail -f logs/mcp_server.log

# Check for MCP errors
grep -i error logs/mcp_server.log

# See MCP startup sequence
head -20 logs/mcp_server.log
```

### 🔌 Integration Points

#### With Agents
- Credit Risk Agent can use MCP tools for enhanced scoring
- Document Agent can send extracted data to MCP for analysis
- Routing Agent can coordinate MCP tool usage

#### With Claude Desktop
- MCP server can be configured in Claude Desktop settings
- Provides direct access to credit tools from Claude interface
- Enables natural language credit assessment queries

### 🚨 Troubleshooting

#### MCP Server Won't Start
```bash
# Check logs for errors
cat logs/mcp_server.log

# Verify dependencies
uv pip list | grep mcp

# Check port conflicts (if using TCP)
lsof -i :3000
```

#### Communication Issues
```bash
# Test MCP server directly
echo '{"method": "ping"}' | python utilities/mcp/servers/credit_mcp_server.py

# Check process status
ps aux | grep credit_mcp_server
```

#### Performance Issues
```bash
# Monitor resource usage
top -p $(cat logs/mcp_server.pid)

# Check memory usage
ps -o pid,ppid,cmd,%mem,%cpu -p $(cat logs/mcp_server.pid)
```

### 📋 Configuration

**Config File**: `utilities/mcp/mcp_config.json`

Key settings:
- Transport method (STDIO)
- Available tools and descriptions
- Server location and startup command
- Client connection details

### 🔄 Lifecycle Management

The MCP server is now fully integrated into the system lifecycle:

1. **Setup**: Installed with `./scripts/manage.sh setup`
2. **Start**: Included in `./scripts/manage.sh start-all`
3. **Monitor**: Available in `./scripts/monitor_logs.sh`
4. **Status**: Checked in `./scripts/manage.sh status`
5. **Stop**: Included in `./scripts/manage.sh stop-all`

### 💡 Best Practices

- Always use the management scripts for consistency
- Monitor logs regularly for performance insights
- Use `start-all` for full system startup
- Check status before debugging issues
- Restart MCP server if credit tools become unresponsive
