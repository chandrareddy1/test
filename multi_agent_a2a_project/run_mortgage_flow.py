#!/usr/bin/env python3
"""
Router Agent - Complete Mortgage Processing Flow Demo
Demonstrates the full end-to-end mortgage applic                    # Show brief description based on the scenario
                if "Complete" in scenario['name']:
                    print(f"      🏠 Full end-to-end mortgage application processing")
              print("💡 Usage examples:")
        print("   # Run specific scenarios with single PDF")
        print("   python run_mortgage_flow.py --pdf application.pdf --scenarios 1")
        print("   # Run with multiple PDFs (individual processing)")
        print("   python run_mortgage_flow.py --pdfs app1.pdf app2.pdf app3.pdf --scenarios 2")
        print("   # Run with multiple PDFs (batch processing)")
        print("   python run_mortgage_flow.py --pdfs app.pdf bank.pdf tax.pdf --multi-file-mode batch --scenarios 1")
        print("   python run_mortgage_flow.py --pdf-dir /path/to/pdfs --scenarios 2")
        print("   # Run both scenarios")
        print("   python run_mortgage_flow.py --pdf application.pdf --scenarios 1,2")    elif "Extraction" in scenario['name']:
                    print(f"      📊 Extract and structure document data")      # Show brief description based on the scenario
                if "Complete" in scenario['name']:
                    print(f"      🏠 Full end-to-end mortgage application processing")
                elif "Extraction" in scenario['name']:
                    print(f"      📊 Extract and structure document data")
                elif "Credit Risk" in scenario['name']:
                    print(f"      💰 Assess financial risk using sample data (independent)")    # Show brief description based on the scenario
                if "Complete" in scenario['name']:
                    print(f"      🏠 Full end-to-end mortgage application processing")
                elif "Extraction" in scenario['name']:
                    print(f"      📊 Extract and structure document data")
                elif "Credit Risk" in scenario['name']:
                    print(f"      💰 Assess financial risk using sample data (independent)")
                elif "Compliance" in scenario['name']:
                    print(f"      ⚖️ Review regulatory and documentation compliance")cessing workflow
"""

import asyncio
import sys
import os
import argparse
import json
from pathlib import Path

# Add the project root to the Python path
import sys
from pathlib import Path

# Get the project root directory dynamically
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from utilities.a2a.agent_connect import AgentConnector
from a2a.types import AgentCard, AgentSkill, AgentCapabilities

def validate_pdf_file(pdf_path: str) -> dict:
    """Simple PDF validation function to replace PDFManager."""
    pdf_file = Path(pdf_path)
    
    # Use dynamic project root for paths
    project_root = Path(__file__).resolve().parent
    
    # Check if file exists with different search paths
    search_paths = [
        pdf_file,
        project_root / "mortgage_docs" / "input" / pdf_file.name,
        project_root / "mortgage_docs" / pdf_file.name,
        Path(f"./{pdf_file.name}")
    ]
    
    for path in search_paths:
        if path.exists() and path.is_file() and path.suffix.lower() == '.pdf':
            try:
                # Test if file is readable
                with open(path, 'rb') as f:
                    f.read(1024)  # Try to read first 1KB
                return {
                    'exists': True,
                    'is_readable': True,
                    'path': str(path),
                    'name': path.name
                }
            except (PermissionError, OSError):
                continue
    
    return {
        'exists': False,
        'is_readable': False,
        'path': pdf_path,
        'name': Path(pdf_path).name
    }

def find_pdfs_in_directory(directory: str) -> list:
    """Find all PDF files in a directory."""
    pdf_files = []
    dir_path = Path(directory)
    
    if dir_path.exists() and dir_path.is_dir():
        for pdf_file in dir_path.glob("*.pdf"):
            if pdf_file.is_file():
                try:
                    # Test if file is readable
                    with open(pdf_file, 'rb') as f:
                        f.read(1024)
                    pdf_files.append({
                        'path': str(pdf_file),
                        'name': pdf_file.name
                    })
                except (PermissionError, OSError):
                    continue
    
    return pdf_files

async def run_mortgage_processing_flow(pdf_path: str = None, selected_scenario_indices: list = None, batch_request: str = None):
    """Run the complete mortgage processing workflow"""
    
    print("🏠 Mortgage Application Processing - Complete Flow")
    print("=" * 60)
    print("🎯 Objective: Process mortgage application through Router Agent")
    print("📋 Flow: PDF Analysis → Credit Risk Assessment → Final Decision")
    print("=" * 60)
    
    # Handle PDF file selection
    if pdf_path:
        # Use provided PDF path
        pdf_info = validate_pdf_file(pdf_path)
        if not pdf_info['exists'] or not pdf_info['is_readable']:
            print(f"❌ Cannot access PDF file: {pdf_path}")
            return
        print(f"📄 Using PDF file: {pdf_info['name']}")
        selected_pdf = pdf_info['path']
    else:
        # Interactive PDF selection - PDF is required for mortgage processing
        print("\n📄 PDF File Selection (Required for mortgage processing):")
        print("   Enter PDF file path:")
        
        custom_path = input("PDF file path: ").strip()
        if not custom_path:
            print("❌ PDF file is required for mortgage processing")
            return
            
        pdf_info = validate_pdf_file(custom_path)
        if pdf_info['exists'] and pdf_info['is_readable']:
            selected_pdf = pdf_info['path']
            print(f"✅ Using: {pdf_info['name']}")
        else:
            print(f"❌ Cannot access: {custom_path}")
            print("❌ PDF file is required for mortgage processing")
            return
    
    # Create Router Agent connection
    router_card = AgentCard(
        name="router_agent",
        description="LangGraph-powered intelligent routing agent",
        url="http://localhost:10004/",
        version="1.0.0",
        defaultInputModes=["text/plain"],
        defaultOutputModes=["text/plain"],
        skills=[AgentSkill(
            id="intelligent_routing_skill",
            name="intelligent_routing_skill", 
            description="Routes and orchestrates tasks across multiple agents",
            tags=["routing", "orchestration", "langgraph"],
            examples=["Route mortgage application through document and credit analysis"]
        )],
        capabilities=AgentCapabilities(streaming=True, pushNotifications=True)
    )
    
    try:
        print("🔌 Connecting to Router Agent...")
        connector = AgentConnector(router_card)
        
        # Mortgage application scenarios - each scenario is independent
        if batch_request:
            # Use batch request for multi-file processing
            scenarios = [
                {
                    "name": "Batch Multi-File Analysis",
                    "request": batch_request,
                    "session": "mortgage_batch_001"
                }
            ]
        else:
            # Regular single-file scenarios
            import uuid
            file_id = uuid.uuid4().hex[:8]
            scenarios = [
                {
                    "name": "Complete Mortgage Application Analysis",
                    "request": f"I need to process a mortgage application. I have a PDF file at {selected_pdf} with applicant information. Please analyze the document, extract the data, assess credit risk, and provide a comprehensive evaluation.",
                    "session": f"mortgage_app_pdf_{file_id}"
                },
                {
                    "name": "Document Data Extraction Only",
                    "request": f"Extract and analyze data from the mortgage application PDF at {selected_pdf}. Focus on applicant financial information, loan details, and property information. Provide a structured summary of the extracted data.",
                    "session": f"doc_process_pdf_{file_id}"
                }
            ]
        
        # Let user choose which scenarios to run
        if selected_scenario_indices:
            # Use pre-selected scenarios from command line
            selected_scenarios = []
            for idx in selected_scenario_indices:
                if 0 <= idx - 1 < len(scenarios):
                    selected_scenarios.append(scenarios[idx - 1])
                else:
                    print(f"⚠️ Invalid scenario number: {idx}")
            
            if selected_scenarios:
                scenario_names = [s['name'] for s in selected_scenarios]
                print(f"✅ Running {len(selected_scenarios)} pre-selected scenarios:")
                for name in scenario_names:
                    print(f"   • {name}")
            else:
                print("❌ No valid scenarios from command line")
                return
        else:
            # Interactive scenario selection
            print(f"\n📋 Available Scenarios ({len(scenarios)} total):")
            print("=" * 50)
            for i, scenario in enumerate(scenarios, 1):
                print(f"   {i}. {scenario['name']}")
                # Show brief description based on the scenario
                if "Complete" in scenario['name']:
                    print(f"      🏠 Full end-to-end mortgage application processing")
                elif "Extraction" in scenario['name']:
                    print(f"      � Extract and structure document data")
                elif "Credit Risk" in scenario['name']:
                    print(f"      💰 Assess financial risk and lending decision")
                elif "Compliance" in scenario['name']:
                    print(f"      ⚖️ Review regulatory and documentation compliance")
            print("=" * 50)
            
            print(f"\n🎯 Scenario Selection Options:")
            print("   • Enter '1' for complete analysis")
            print("   • Enter '2' for document extraction only") 
            print("   • Enter '1,2' for both scenarios")
            
            choice = input(f"\nSelect scenarios (1-{len(scenarios)}): ").strip()
            
            # Parse user choice - no default, must specify
            selected_scenarios = []
            if not choice:
                print("❌ You must specify which scenarios to run")
                return
            
            try:
                if ',' in choice:
                    # Multiple scenarios selected
                    indices = [int(x.strip()) - 1 for x in choice.split(',')]
                else:
                    # Single scenario selected
                    indices = [int(choice.strip()) - 1]
                
                for idx in indices:
                    if 0 <= idx < len(scenarios):
                        selected_scenarios.append(scenarios[idx])
                    else:
                        print(f"⚠️ Skipping invalid scenario number: {idx + 1}")
                
                if selected_scenarios:
                    scenario_names = [s['name'] for s in selected_scenarios]
                    print(f"✅ Running {len(selected_scenarios)} selected scenarios:")
                    for name in scenario_names:
                        print(f"   • {name}")
                else:
                    print("❌ No valid scenarios selected")
                    return
                    
            except ValueError:
                print("❌ Invalid input format. Use numbers like: 1, 2, or 1,3")
                return
        
        # Run selected scenarios
        for i, scenario in enumerate(selected_scenarios, 1):
            print(f"\n📋 SCENARIO {i}: {scenario['name']}")
            print("-" * 50)
            print(f"📝 Request: {scenario['request'][:80]}...")
            print(f"🔗 Session: {scenario['session']}")
            
            try:
                print(f"\n🚀 Sending request to Router Agent...")
                print("🔄 Waiting for response...\n")
                
                # Send task and get response
                result = await connector.send_task(scenario['request'], scenario['session'])
                
                print(f"✅ Router Agent Response Received")
                print(f"🔍 Response Type: {type(result)}")
                
                # Extract and display the response content
                if hasattr(result, 'content'):
                    response_text = result.content
                elif isinstance(result, str):
                    response_text = result
                elif isinstance(result, dict):
                    # If it's a dict, try to extract meaningful content
                    response_text = json.dumps(result, indent=2)
                else:
                    response_text = str(result)
                
                # Display the full response
                print(f"\n📊 FULL AGENT OUTPUT:")
                print("=" * 60)
                print(response_text)
                print("=" * 60)
                
                # Also show some analysis of the response
                if response_text and len(response_text) > 0:
                    lines = response_text.split('\n')
                    print(f"📈 Response Stats:")
                    print(f"   • Total characters: {len(response_text)}")
                    print(f"   • Total lines: {len(lines)}")
                    print(f"   • Non-empty lines: {len([l for l in lines if l.strip()])}")
                else:
                    print("⚠️ Empty or no response received")
                
            except Exception as e:
                print(f"❌ Scenario {i} failed: {str(e)}")
                print(f"🔍 Error type: {type(e).__name__}")
                
                # Show detailed error information
                import traceback
                print(f"\n🔧 Detailed error trace:")
                traceback.print_exc()
                
                # Check if it's a connection issue
                if "Connection" in str(e) or "timeout" in str(e).lower():
                    print(f"\n� Connection troubleshooting:")
                    print("   1. Make sure Router Agent is running:")
                    print("      uv run python -m src.agents.router_agent --host localhost --port 10004")
                    print("   2. Check if port 10004 is available")
                    print("   3. Verify the agent is responding:")
                    print("      curl http://localhost:10004/.well-known/agent.json")
        
        print(f"\n🎉 Complete Mortgage Processing Flow Demonstration Finished!")
        print("=" * 60)
        print("📊 Summary:")
        print("   • Router Agent orchestrated multi-agent workflows")
        print("   • Document processing and credit analysis coordinated")
        print("   • Real-time task routing and execution")
        print("   • End-to-end mortgage application processing")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Flow execution failed: {e}")
        print("🔍 Make sure the Router Agent is running on http://localhost:10004")
        print("💡 Start it with: uv run python -m src.agents.router_agent --host localhost --port 10004")

async def run_simple_flow():
    """Run a simple single request flow with detailed output"""
    print("🚀 Simple Mortgage Processing Request")
    print("=" * 40)
    
    router_card = AgentCard(
        name="router_agent",
        description="Router Agent",
        url="http://localhost:10004/",
        version="1.0.0",
        defaultInputModes=["text/plain"],
        defaultOutputModes=["text/plain"],
        skills=[AgentSkill(id="routing", name="routing", description="routing", tags=[], examples=[])],
        capabilities=AgentCapabilities(streaming=True, pushNotifications=True)
    )
    
    try:
        connector = AgentConnector(router_card)
        
        request = "Analyze mortgage application for applicant with $8000 monthly income, $2500 monthly debts, credit score 720, requesting $400,000 loan"
        print(f"📝 Request: {request}")
        print("\n🔄 Sending to Router Agent...\n")
        
        # Send the request
        result = await connector.send_task(request, "simple_flow_001")
        
        # Display the response
        if hasattr(result, 'content'):
            response_text = result.content
        elif isinstance(result, str):
            response_text = result
        elif isinstance(result, dict):
            response_text = json.dumps(result, indent=2)
        else:
            response_text = str(result)
        
        print("📊 AGENT OUTPUT:")
        print("=" * 50)
        print(response_text)
        print("=" * 50)
        print("✅ Simple flow complete!")
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        print("🔧 Troubleshooting:")
        print("   1. Make sure Router Agent is running:")
        print("      uv run python -m src.agents.router_agent --host localhost --port 10004")
        print("   2. Test agent connectivity:")
        print("      curl http://localhost:10004/.well-known/agent.json")
        
        # Show detailed error
        import traceback
        print(f"\n🔍 Detailed error:")
        traceback.print_exc()

if __name__ == "__main__":
    import sys
    
    parser = argparse.ArgumentParser(description="Mortgage Processing Flow - PDF Required for All Scenarios")
    parser.add_argument("--pdf", type=str, help="Path to PDF file to process (required)")
    parser.add_argument("--pdfs", type=str, nargs='+', help="Multiple PDF file paths to process")
    parser.add_argument("--pdf-dir", type=str, help="Directory to search for PDF files")
    parser.add_argument("--simple", action="store_true", help="Run simple flow instead of full demo")
    parser.add_argument("--scenarios", type=str, help="Comma-separated scenario numbers to run (e.g., '1,3' or '2')")
    parser.add_argument("--list-scenarios", action="store_true", help="List available scenarios and exit")
    parser.add_argument("--multi-file-mode", choices=['individual', 'batch'], default='individual', 
                        help="Multi-file processing mode: 'individual' (separate analysis) or 'batch' (comparative)")
    
    args = parser.parse_args()
    
    # Handle scenario listing
    if args.list_scenarios:
        print("📋 Available Scenarios (PDF required for all scenarios):")
        print("\n🏠 Mortgage Processing Scenarios:")
        print("   1. Complete Mortgage Application Analysis - Full end-to-end processing")
        print("   2. Document Data Extraction Only - Extract data from PDF")
        print("\n💡 Usage examples:")
        print("   # Run specific scenarios with PDF")
        print("   python run_mortgage_flow.py --pdf application.pdf --scenarios 1")
        print("   python run_mortgage_flow.py --pdf-dir /path/to/pdfs --scenarios 2")
        print("   # Run both scenarios")
        print("   python run_mortgage_flow.py --pdf application.pdf --scenarios 1,2")
        sys.exit(0)
    
    # Parse scenario selection
    selected_scenario_indices = None
    if args.scenarios:
        try:
            selected_scenario_indices = [int(x.strip()) for x in args.scenarios.split(',')]
            print(f"🎯 Pre-selected scenarios: {selected_scenario_indices}")
        except ValueError:
            print(f"❌ Invalid scenario format: {args.scenarios}")
            print("Use comma-separated numbers like: 1,3 or just 2")
            sys.exit(1)
    
    
    if args.simple:
        asyncio.run(run_simple_flow())
    else:
        # Check if PDF is provided (single file, multiple files, or directory)
        pdf_files = []
        
        if args.pdfs:
            # Multiple PDFs provided
            pdf_files = args.pdfs
            print(f"🗂️ Processing {len(pdf_files)} PDF files in {args.multi_file_mode} mode")
            
            # Validate all files exist
            valid_files = []
            for pdf_path in pdf_files:
                pdf_info = validate_pdf_file(pdf_path)
                if pdf_info['exists'] and pdf_info['is_readable']:
                    valid_files.append(pdf_path)
                else:
                    print(f"⚠️ Skipping invalid PDF: {pdf_path}")
            
            if not valid_files:
                print("❌ No valid PDF files found")
                sys.exit(1)
            
            pdf_files = valid_files
            
        elif args.pdf:
            # Single PDF provided
            pdf_files = [args.pdf]
            
        elif args.pdf_dir:
            # Directory search
            pdfs = find_pdfs_in_directory(args.pdf_dir)
            if pdfs:
                pdf_files = [pdf['path'] for pdf in pdfs]
                print(f"📁 Found {len(pdf_files)} PDF files in {args.pdf_dir}")
            else:
                print(f"❌ No PDF files found in {args.pdf_dir}")
                sys.exit(1)
        else:
            print("❌ PDF file(s) required for mortgage processing")
            print("💡 Usage:")
            print("   python run_mortgage_flow.py --pdf application.pdf --scenarios 1,3")
            print("   python run_mortgage_flow.py --pdfs app1.pdf app2.pdf --scenarios 2")
            print("   python run_mortgage_flow.py --pdf-dir /path/to/pdfs --scenarios 2")
            print("   python run_mortgage_flow.py --list-scenarios  # to see available scenarios")
            sys.exit(1)
        
        # Process the files
        if len(pdf_files) == 1:
            # Single file processing
            asyncio.run(run_mortgage_processing_flow(pdf_files[0], selected_scenario_indices=selected_scenario_indices))
        else:
            # Multi-file processing
            print(f"🔄 Multi-file processing mode: {args.multi_file_mode}")
            if args.multi_file_mode == 'batch':
                # Process all files together in one request
                file_list = ", ".join([f"{Path(p).name} at {p}" for p in pdf_files])
                batch_request = f"I need to process multiple mortgage application documents. I have {len(pdf_files)} PDF files: {file_list}. Please analyze all documents together, extract data from each, and provide comparative analysis with individual summaries."
                asyncio.run(run_mortgage_processing_flow(pdf_files[0], selected_scenario_indices=selected_scenario_indices, batch_request=batch_request))
            else:
                # Process files individually
                for i, pdf_file in enumerate(pdf_files, 1):
                    print(f"\n📄 Processing file {i}/{len(pdf_files)}: {Path(pdf_file).name}")
                    asyncio.run(run_mortgage_processing_flow(pdf_file, selected_scenario_indices=selected_scenario_indices))
                    if i < len(pdf_files):
                        print(f"⏳ Moving to next file...")
                        import time
                        time.sleep(2)  # Brief pause between files
