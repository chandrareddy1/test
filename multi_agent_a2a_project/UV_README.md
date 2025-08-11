# 🏠 Mortgage Application Processor - UV Setup Guide

A modern multi-agent mortgage processing system with Streamlit frontend, managed by UV for fast and reliable dependency management.

## 🚀 Quick Start with UV

### 1. Initial Setup

```bash
# Run the UV setup script (installs UV if needed)
./setup_uv.sh
```

This will:
- Install UV if not already present
- Create a virtual environment
- Install all project dependencies
- Set up the development environment

### 2. Start Backend Agents

```bash
# Start all agents using UV
./start_all_agents.sh
```

### 3. Launch Streamlit Frontend

```bash
# Start the web interface using UV
./start_streamlit_app.sh
```

The app will open at `http://localhost:8501`

## 📦 UV Commands

### Basic Operations
```bash
# Install dependencies
uv pip install -e .

# Install with optional dependencies
uv pip install -e .[dev]        # Development dependencies
uv pip install -e .[streamlit]  # Streamlit-only installation

# Run commands in the virtual environment
uv run python run_mortgage_flow.py --help
uv run streamlit run streamlit_mortgage_app.py
uv run pytest tests/
```

### Development Workflow
```bash
# Activate virtual environment manually
source .venv/bin/activate

# Add new dependencies
uv add streamlit plotly pandas

# Add development dependencies
uv add --dev pytest black isort

# Update dependencies
uv pip install --upgrade-strategy eager -e .

# Lock dependencies
uv pip freeze > requirements.lock
```

## 🔧 Project Structure

```
├── pyproject.toml                 # UV project configuration
├── setup_uv.sh                   # UV setup script
├── start_all_agents.sh           # Start agents with UV
├── start_streamlit_app.sh        # Start Streamlit with UV
├── streamlit_mortgage_app.py      # Main Streamlit application
├── src/agents/                   # Agent modules
│   ├── document_agent/
│   ├── credit_risk_agent/
│   ├── compliance_agent/
│   └── routing_agent/
├── utilities/                    # Shared utilities
├── mortgage_docs/               # Document storage
└── logs/                       # Agent logs
```

## 📋 Dependencies

### Core Dependencies
- **A2A SDK**: Agent-to-agent communication
- **LangChain/LangGraph**: LLM orchestration and workflows
- **CrewAI**: Multi-agent framework
- **Streamlit**: Web frontend
- **PDFPlumber**: PDF processing
- **ReportLab**: PDF generation

### Optional Dependencies
- **Development**: `pytest`, `black`, `isort`, `mypy`
- **Streamlit-only**: Minimal frontend installation

## 🎯 Available Commands

### Agent Management
```bash
./start_all_agents.sh     # Start all agents
./stop_all_agents.sh      # Stop all agents
```

### Frontend
```bash
./start_streamlit_app.sh  # Start web interface
uv run streamlit run streamlit_mortgage_app.py
```

### CLI Processing
```bash
# Process single PDF
uv run python run_mortgage_flow.py --pdf mortgage_docs/input/app.pdf --scenarios 1

# Process multiple PDFs
uv run python run_mortgage_flow.py --pdfs *.pdf --scenarios 1,2

# See all options
uv run python run_mortgage_flow.py --help
```

## 🔧 Configuration

### UV Configuration (`pyproject.toml`)
```toml
[tool.uv]
dev-dependencies = [
    "pytest>=7.0.0",
    "black>=23.0.0",
    # ... other dev deps
]

[project.optional-dependencies]
streamlit = [
    "streamlit>=1.48.0",
    "pandas>=2.3.1",
    # ... streamlit deps
]
```

### Environment Variables
Create a `.env` file:
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

## 🛠️ Troubleshooting

### UV Issues
```bash
# Reinstall UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Rebuild virtual environment
rm -rf .venv
uv venv
uv pip install -e .

# Check UV version
uv --version
```

### Agent Issues
```bash
# Check agent logs
tail -f logs/document_agent.log
tail -f logs/routing_agent.log

# Restart specific agent
./stop_all_agents.sh
uv run python src/agents/document_agent/__main__.py &
```

### Dependencies
```bash
# Check installed packages
uv pip list

# Verify environment
uv pip check

# Update all packages
uv pip install --upgrade-strategy eager -e .
```

## 🌟 Benefits of UV

- **Fast**: 10-100x faster than pip
- **Reliable**: Consistent dependency resolution
- **Simple**: Single tool for environment and package management
- **Compatible**: Works with existing pip/pyproject.toml projects
- **Modern**: Built for Python 3.7+ with full typing support

## 🔄 Migration from pip

If you have an existing pip-based setup:

```bash
# Remove old virtual environment
rm -rf venv

# Run UV setup
./setup_uv.sh

# Your pyproject.toml will be used automatically
```

## 📝 Development

### Adding Dependencies
```bash
# Runtime dependency
uv add langchain

# Development dependency  
uv add --dev pytest

# Optional dependency group
uv add --optional streamlit plotly
```

### Code Quality
```bash
# Format code
uv run black .
uv run isort .

# Type checking
uv run mypy src/

# Run tests
uv run pytest
```

## 🚀 Production Deployment

```bash
# Create production requirements
uv pip compile pyproject.toml -o requirements.txt

# Install in production
pip install -r requirements.txt

# Or use UV in production
uv pip install -e .
```

---

**Need Help?** Check the logs in `logs/` directory or run `uv --help` for UV-specific commands.
