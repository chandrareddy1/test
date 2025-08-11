# 🏠 Mortgage Application Processor - Streamlit Frontend

A modern web interface for processing mortgage applications using AI-powered multi-agent systems.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Recommended: Use UV for modern dependency management
./setup_uv.sh

# Or install Streamlit dependencies only
uv pip install -e .[streamlit]

# Or install all project dependencies  
uv sync
```

### 2. Start All Agents

```bash
# Start all backend agents
./start_all_agents.sh
```

This will start:
- Document Agent (Port 10001)
- Credit Risk Agent (Port 10002) 
- Compliance Agent (Port 10003)
- Routing Agent (Port 10004)

### 3. Launch Streamlit App

```bash
# Start the web interface
./start_streamlit_app.sh
```

The app will open automatically in your browser at `http://localhost:8501`

## 🖥️ Using the Web Interface

### Upload & Process
1. **Upload PDF**: Click "Browse files" to select your mortgage application PDF
2. **Process**: Click "🚀 Process Application" to analyze the document
3. **Review**: Examine results across multiple tabs
4. **Download**: Get your comprehensive PDF report

### Interface Sections

#### 📊 Summary Tab
- Key applicant information
- Credit score and risk level
- Application approval status
- Confidence metrics

#### 📄 Document Data Tab
- Extracted personal information
- Financial details from PDF
- Additional document metadata

#### ⚖️ Risk Assessment Tab
- Credit risk analysis
- Risk factors and recommendations
- Debt-to-income calculations
- Loan-to-value ratios

#### ✅ Compliance Tab
- Regulatory compliance status
- Compliance issues (if any)
- Recommendations for improvement
- Detailed compliance metrics

#### 📋 Executive Summary Tab
- AI-generated summary
- Key findings and recommendations
- Final decision rationale

## 🔧 Management Scripts

### Start Services
```bash
./start_all_agents.sh      # Start all backend agents
./start_streamlit_app.sh   # Start web interface
```

### Stop Services
```bash
./stop_all_agents.sh       # Stop all backend agents
# Ctrl+C in Streamlit terminal to stop web interface
```

### Check Status
The Streamlit app will show agent status in the sidebar:
- ✅ Green: Agent running and responsive
- ❌ Red: Agent not available

## 📁 File Structure

```
streamlit_mortgage_app.py     # Main Streamlit application
start_streamlit_app.sh        # Web interface startup script
start_all_agents.sh          # Backend agents startup script
stop_all_agents.sh           # Stop all agents script
pyproject.toml               # UV-based dependency configuration
logs/                        # Agent log files
temp_uploads/               # Temporary PDF storage
```

## 🛠️ Troubleshooting

### Agents Not Starting
```bash
# Check if ports are already in use
netstat -an | grep -E "(10001|10002|10003|10004)"

# Kill processes on agent ports if needed
./stop_all_agents.sh
```

### Streamlit Issues
```bash
# Clear Streamlit cache
streamlit cache clear

# Run with verbose output
streamlit run streamlit_mortgage_app.py --logger.level debug
```

### PDF Processing Errors
- Ensure PDF is a valid mortgage application document
- Check file size (< 50MB recommended)
- Verify PDF is not password protected

## 🎨 Features

### Real-time Processing
- Live agent status monitoring
- Progress indicators during processing
- Immediate result display

### Comprehensive Analysis
- Document data extraction using OCR
- Credit risk assessment with MCP tools
- Regulatory compliance checking
- Executive summary generation

### Professional Reports
- Downloadable PDF reports
- Formatted compliance documentation
- Executive summary with recommendations

### User-Friendly Interface
- Drag-and-drop file upload
- Tabbed result organization
- Visual status indicators
- Responsive design

## 🔒 Security Notes

- Files are temporarily stored during processing
- Uploaded files are automatically cleaned up
- No permanent storage of sensitive data
- All processing happens locally

## 📊 Supported Document Types

- Mortgage application PDFs
- Structured mortgage forms
- Bank statements (future enhancement)
- Credit reports (future enhancement)

## 🤝 Integration

The Streamlit frontend integrates with:
- A2A (Agent-to-Agent) discovery system
- Dynamic agent routing
- Multi-agent workflow processing
- PDF generation and reporting

## 💡 Tips

1. **PDF Quality**: Ensure PDFs are clear and readable for best extraction results
2. **Agent Health**: Monitor the sidebar for agent status before processing
3. **Large Files**: For large PDFs, processing may take 30-60 seconds
4. **Multiple Files**: Process one file at a time for optimal performance

---

**Need Help?** Check the logs in the `logs/` directory for detailed error information.
