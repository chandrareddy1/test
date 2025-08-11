# MortgageInsight Pro - Frontend

**AI-Powered Mortgage Analysis Platform**

## Overview

MortgageInsight Pro is a sophisticated Streamlit-based web application that provides comprehensive mortgage application analysis through an intelligent multi-agent system. The platform offers real-time document processing, risk assessment, compliance checking, and executive reporting.

## Features

### 🎯 Core Capabilities
- **Document Analysis**: AutoGen-powered PDF extraction and data processing
- **Risk Assessment**: SmoAgents-powered credit risk evaluation
- **Compliance Checking**: CrewAI-powered regulatory compliance verification
- **Intelligent Routing**: LangGraph-powered task orchestration
- **Executive Reporting**: Comprehensive PDF report generation

### 🖥️ User Interface
- **Modern Design**: Clean, professional interface with custom styling
- **Real-time Status**: Live agent monitoring in sidebar
- **Tabbed Results**: Organized display of analysis results
- **File Upload**: Drag-and-drop PDF upload functionality
- **PDF Download**: One-click report download

### 📊 Analysis Tabs
1. **Summary**: Key metrics and decision overview
2. **Document Data**: Extracted personal and financial information
3. **Risk Assessment**: Credit analysis with visual indicators
4. **Compliance**: Regulatory compliance status and issues
5. **Executive Summary**: Comprehensive analysis narrative

## Technology Stack

- **Frontend Framework**: Streamlit 1.30+
- **Python**: 3.11+
- **Agent Communication**: A2A Protocol over HTTP
- **Styling**: Custom CSS with professional theme
- **Package Management**: UV (ultrafast Python package manager)

## File Structure

```
frontend/
├── mortgage_analyzer_app.py    # Main Streamlit application
└── README.md                   # This documentation
```

## Quick Start

### Using Scripts (Recommended)
```bash
# Start the complete system
./scripts/manage.sh start-all

# Or start just the frontend (agents must be running)
./scripts/manage.sh start-streamlit

# Check system status
./scripts/manage.sh status
```

### Manual Start
```bash
# Ensure agents are running first
./scripts/start_all_agents.sh

# Start the frontend
uv run streamlit run frontend/mortgage_analyzer_app.py --server.port 8501
```

## Agent Dependencies

The frontend requires all agents to be running:

| Agent | Port | Technology | Purpose |
|-------|------|------------|---------|
| Document Agent | 10001 | AutoGen | PDF processing and data extraction |
| Credit Risk Agent | 10002 | SmoAgents | Credit risk assessment |
| Compliance Agent | 10003 | CrewAI | Regulatory compliance checking |
| Routing Agent | 10004 | LangGraph | Task coordination and routing |

## Configuration

### Theme Settings
- **Primary Color**: `#1f4e79` (Professional blue)
- **Background**: White with light gray secondary
- **Layout**: Wide mode for optimal content display

### Server Settings
- **Port**: 8501 (default)
- **Address**: localhost
- **Headless**: false (opens browser automatically)

## Usage Workflow

1. **Upload PDF**: Select mortgage application PDF file
2. **Process**: Click "Process Application" button
3. **Monitor**: Watch real-time agent status in sidebar
4. **Review**: Examine results across multiple tabs
5. **Download**: Get comprehensive PDF report

## Error Handling

- **Agent Discovery**: Automatic retry with user guidance
- **File Upload**: Size and format validation
- **Processing**: Comprehensive error messages and recovery
- **Network**: Timeout handling and connection retry

## API Integration

The app communicates with agents via the A2A protocol:
- **Discovery**: Automatic agent discovery on startup
- **Communication**: HTTP-based task submission
- **Results**: JSON response parsing and display

## Development

### Local Development
```bash
# Install dependencies
uv sync

# Run in development mode
uv run streamlit run frontend/mortgage_analyzer_app.py --server.runOnSave true
```

### Customization
- Modify CSS styles in the app header
- Update agent instructions in sidebar
- Extend result display functions
- Add new analysis tabs

## Support

For issues or questions:
1. Check agent status using `./scripts/manage.sh status`
2. Review logs in `logs/` directory
3. Restart system using `./scripts/manage.sh restart-all`

## Version History


