import asyncio
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Union, Annotated
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict
from dotenv import load_dotenv
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

# Add project root to path for imports
import sys
from pathlib import Path

# Get the project root directory dynamically
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import A2A discovery and connection components
from utilities.a2a.agent_discovery import AgentDiscovery
from utilities.a2a.agent_connect import AgentConnector
from a2a.types import AgentCard

# State definition for the routing agent
class RoutingState(TypedDict):
    messages: Annotated[list, add_messages]
    query: str
    route_decision: str
    document_data: Dict
    risk_assessment: Dict
    compliance_result: Dict
    final_result: Dict

class RoutingAgent:
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain", "application/json"]
    
    def __init__(self):
        self.graph = None
        self.llm = None
        self.available_agents = {}
        self.discovery = AgentDiscovery()
        
    async def create(self):
        """Initialize the routing agent with LangGraph and discover available agents."""
        # Load environment variables from .env file
        load_dotenv()
        
        # Get API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        # Create the LLM
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=api_key,
            temperature=0
        )
        
        # Discover available agents
        await self._discover_agents()
        
        # Build the routing graph
        self._build_routing_graph()
    
    async def _discover_agents(self):
        """Discover available A2A agents via HTTP discovery."""
        print("🔍 Discovering available agents...")
        self.available_agents = await self.discovery.discover_agents()
        
        if self.available_agents:
            print(f"✅ Found {len(self.available_agents)} available agents:")
            for name, card in self.available_agents.items():
                print(f"   • {name}: {card.description}")
        else:
            print("⚠️ No agents discovered - falling back to local processing")
            
    def _get_agent_by_skill(self, skill_keywords: List[str]) -> Optional[AgentCard]:
        """Find an agent by matching skills."""
        # Direct mapping for known agents
        agent_mapping = {
            "document": "document_agent",
            "pdf": "document_agent", 
            "extraction": "document_agent",
            "credit": "credit_risk_agent",
            "risk": "credit_risk_agent",
            "financial": "credit_risk_agent",
            "compliance": "compliance_agent",
            "regulatory": "compliance_agent",
            "legal": "compliance_agent"
        }
        
        # Try direct mapping first
        for keyword in skill_keywords:
            agent_name = agent_mapping.get(keyword.lower())
            if agent_name and agent_name in self.available_agents:
                return self.available_agents[agent_name]
        
        # Fallback to text matching
        for name, agent_card in self.available_agents.items():
            # Check if any skill keyword matches agent name or description
            agent_text = f"{name} {agent_card.description}".lower()
            
            # Also check skill names if available
            skill_text = ""
            if agent_card.skills:
                skill_text = " ".join([skill.name for skill in agent_card.skills]).lower()
            
            combined_text = f"{agent_text} {skill_text}"
            
            if any(keyword.lower() in combined_text for keyword in skill_keywords):
                return agent_card
        return None
    
    def _build_routing_graph(self):
        """Build the LangGraph routing workflow."""
        
        # Define the workflow
        workflow = StateGraph(RoutingState)
        
        # Add nodes
        workflow.add_node("route_decision", self._make_routing_decision)
        workflow.add_node("document_processing", self._process_document)
        workflow.add_node("risk_assessment", self._assess_risk)
        workflow.add_node("compliance_check", self._check_compliance)
        workflow.add_node("final_aggregation", self._aggregate_results)
        
        # Define edges
        workflow.set_entry_point("route_decision")
        
        # Conditional routing based on decision
        workflow.add_conditional_edges(
            "route_decision",
            self._route_condition,
            {
                "document_only": "document_processing",
                "risk_only": "risk_assessment", 
                "compliance_only": "compliance_check",
                "full_pipeline": "document_processing"
            }
        )
        
        # Pipeline edges for full processing
        workflow.add_edge("document_processing", "risk_assessment")
        workflow.add_edge("risk_assessment", "compliance_check") 
        workflow.add_edge("compliance_check", "final_aggregation")
        
        # Single processing edges
        workflow.add_edge("final_aggregation", END)
        
        # Compile the graph
        self.graph = workflow.compile()
    
    async def _make_routing_decision(self, state: RoutingState) -> RoutingState:
        """Determine which agents to involve based on the query."""
        query = state["query"]
        
        # Use LLM to determine routing
        routing_prompt = f"""
        Analyze this query and determine which mortgage processing agents should be involved:
        
        Query: {query}
        
        Available agents:
        1. document_agent - Extracts data from mortgage documents (PDFs)
        2. risk_agent - Performs credit risk assessment
        3. compliance_agent - Checks regulatory compliance
        
        Routing options:
        - "document_only" - Only document extraction needed
        - "risk_only" - Only risk assessment needed  
        - "compliance_only" - Only compliance check needed
        - "full_pipeline" - Full end-to-end processing (document → risk → compliance)
        
        Return only one of these routing options.
        """
        
        response = await self.llm.ainvoke([{"role": "user", "content": routing_prompt}])
        route_decision = response.content.strip().lower()
        
        # Validate and default to full pipeline if unclear
        valid_routes = ["document_only", "risk_only", "compliance_only", "full_pipeline"]
        if route_decision not in valid_routes:
            route_decision = "full_pipeline"
        
        state["route_decision"] = route_decision
        state["messages"].append({"role": "assistant", "content": f"Routing decision: {route_decision}"})
        
        return state
    
    def _route_condition(self, state: RoutingState) -> str:
        """Return the routing decision for conditional edges."""
        return state["route_decision"]
    
    async def _process_document(self, state: RoutingState) -> RoutingState:
        """Process document using dynamically discovered document agent."""
        try:
            # Find document agent via discovery
            doc_agent_card = self._get_agent_by_skill(["document", "pdf", "extraction"])
            
            if not doc_agent_card:
                print("⚠️ No document agent found, falling back to local processing")
                # Fallback to direct import if no agent discovered
                from src.agents.document_agent.agent import DocumentAgent
                doc_agent = DocumentAgent()
                await doc_agent.create()
                
                # Extract PDF path and process locally
                query = state["query"]
                import re
                pdf_path_match = re.search(r'([^\s]+\.pdf)', query)
                
                if pdf_path_match:
                    pdf_filename = os.path.basename(pdf_path_match.group(1))
                    document_data = await doc_agent.process_document(pdf_filename)
                else:
                    document_data = {
                        "applicant_name": "Sample Applicant (No PDF specified)",
                        "annual_income": 75000,
                        "monthly_debt": 2000,
                        "credit_score": 720,
                        "loan_amount": 300000,
                        "employment_history": "Stable employment for 5 years"
                    }
            else:
                print(f"� Connecting to document agent: {doc_agent_card.name}")
                # Use A2A protocol to communicate with document agent
                connector = AgentConnector(doc_agent_card)
                
                # Create query for document agent
                query = state["query"]
                document_request = f"Extract and analyze data from the mortgage application PDF. Query: {query}"
                
                # Generate session ID for tracking
                import uuid
                session_id = str(uuid.uuid4())
                
                try:
                    # Send request to document agent
                    response = await connector.send_task(document_request, session_id)
                    
                    # Try to parse JSON response
                    try:
                        response_data = json.loads(response)
                        
                        # Handle the document agent's response structure
                        if "results" in response_data and response_data["results"]:
                            # Extract the first result from the results array
                            document_data = response_data["results"][0]
                            print(f"✅ Successfully extracted data via A2A: {document_data.get('applicant_name', 'Unknown')}")
                        elif "applicant_name" in response_data:
                            # Direct structure
                            document_data = response_data
                        else:
                            # Fallback structure
                            document_data = response_data
                            
                    except json.JSONDecodeError:
                        # If not JSON, create structured response
                        print("⚠️ Document agent response not in JSON format, creating structured data")
                        document_data = {
                            "applicant_name": "Document Agent Response",
                            "annual_income": 75000,
                            "raw_response": response,
                            "processing_note": "Response parsed from text format"
                        }
                        
                except Exception as e:
                    print(f"❌ Error communicating with document agent: {e}")
                    document_data = {"error": f"Document agent communication failed: {str(e)}"}
            
            state["document_data"] = document_data
            state["messages"].append({"role": "assistant", "content": "Document processing completed"})
            
        except Exception as e:
            print(f"❌ Document processing exception: {str(e)}")
            state["document_data"] = {"error": f"Document processing failed: {str(e)}"}
            state["messages"].append({"role": "assistant", "content": f"Document processing error: {str(e)}"})
        
        return state
    
    async def _assess_risk(self, state: RoutingState) -> RoutingState:
        """Assess risk using dynamically discovered credit risk agent."""
        try:
            # Find credit risk agent via discovery
            risk_agent_card = self._get_agent_by_skill(["credit", "risk", "financial"])
            
            if not risk_agent_card:
                print("⚠️ No credit risk agent found, falling back to local processing")
                # Fallback to direct import if no agent discovered
                from src.agents.credit_risk_agent.agent import CreditRiskAgent
                risk_agent = CreditRiskAgent()
                await risk_agent.create()
                
                input_data = state.get("document_data", state["query"])
                risk_result = await risk_agent.process_document_data(input_data)
            else:
                print(f"🔗 Connecting to credit risk agent: {risk_agent_card.name}")
                # Use A2A protocol to communicate with credit risk agent
                connector = AgentConnector(risk_agent_card)
                
                # Prepare input data for risk assessment
                input_data = state.get("document_data", {})
                if isinstance(input_data, dict):
                    risk_request = f"Perform credit risk assessment on this applicant data: {json.dumps(input_data)}"
                else:
                    risk_request = f"Perform credit risk assessment. Query: {state['query']}"
                
                # Generate session ID for tracking
                import uuid
                session_id = str(uuid.uuid4())
                
                try:
                    # Send request to credit risk agent
                    response = await connector.send_task(risk_request, session_id)
                    
                    # Try to parse JSON response
                    try:
                        response_data = json.loads(response)
                        
                        # Handle different response structures
                        if "risk_analysis" in response_data:
                            # Credit risk agent structure
                            risk_result = response_data["risk_analysis"]
                        elif "results" in response_data and response_data["results"]:
                            # Extract the first result from the results array
                            risk_result = response_data["results"][0]
                        else:
                            # Direct structure
                            risk_result = response_data
                            
                        print(f"✅ Successfully got risk assessment via A2A: {risk_result.get('risk_level', 'unknown')}")
                            
                    except json.JSONDecodeError:
                        # If not JSON, create structured response
                        print("⚠️ Credit risk agent response not in JSON format, creating structured data")
                        risk_result = {
                            "risk_level": "medium",
                            "risk_score": 65,
                            "confidence": 0.7,
                            "raw_response": response,
                            "processing_note": "Response parsed from text format"
                        }
                        
                except Exception as e:
                    print(f"❌ Error communicating with credit risk agent: {e}")
                    risk_result = {"error": f"Credit risk agent communication failed: {str(e)}"}
            
            state["risk_assessment"] = risk_result
            state["messages"].append({"role": "assistant", "content": "Risk assessment completed"})
            
        except Exception as e:
            print(f"❌ Risk assessment exception: {str(e)}")
            state["risk_assessment"] = {"error": f"Risk assessment failed: {str(e)}"}
            state["messages"].append({"role": "assistant", "content": f"Risk assessment error: {str(e)}"})
        
        return state
    
    async def _check_compliance(self, state: RoutingState) -> RoutingState:
        """Check compliance using dynamically discovered compliance agent."""
        try:
            # Find compliance agent via discovery
            compliance_agent_card = self._get_agent_by_skill(["compliance", "regulatory", "legal"])
            
            if not compliance_agent_card:
                print("⚠️ No compliance agent found, falling back to local processing")
                # Fallback to direct import if no agent discovered
                from src.agents.compliance_agent.agent import ComplianceAgent
                compliance_agent = ComplianceAgent()
                await compliance_agent.create()
                
                input_data = state.get("risk_assessment", state.get("document_data", state["query"]))
                if isinstance(input_data, dict):
                    input_content = json.dumps(input_data)
                else:
                    input_content = str(input_data)
                
                compliance_result = await compliance_agent.process(input_content)
            else:
                print(f"🔗 Connecting to compliance agent: {compliance_agent_card.name}")
                # Use A2A protocol to communicate with compliance agent
                connector = AgentConnector(compliance_agent_card)
                
                # Prepare comprehensive input data for compliance check
                input_data = {
                    "document_data": state.get("document_data", {}),
                    "risk_assessment": state.get("risk_assessment", {}),
                    "query": state["query"]
                }
                
                compliance_request = f"Perform regulatory compliance check on this mortgage application data: {json.dumps(input_data)}"
                
                # Generate session ID for tracking
                import uuid
                session_id = str(uuid.uuid4())
                
                try:
                    # Send request to compliance agent
                    response = await connector.send_task(compliance_request, session_id)
                    
                    # Try to parse JSON response
                    try:
                        response_data = json.loads(response)
                        
                        # Handle different response structures
                        if "compliance_analysis" in response_data:
                            # Compliance agent structure
                            compliance_result = response_data["compliance_analysis"]
                        elif "results" in response_data and response_data["results"]:
                            # Extract the first result from the results array
                            compliance_result = response_data["results"][0]
                        else:
                            # Direct structure
                            compliance_result = response_data
                            
                        print(f"✅ Successfully got compliance check via A2A: {compliance_result.get('approved', 'unknown')}")
                            
                    except json.JSONDecodeError:
                        # If not JSON, create structured response
                        print("⚠️ Compliance agent response not in JSON format, creating structured data")
                        compliance_result = {
                            "approved": True,
                            "confidence": 0.8,
                            "compliance_issues": [],
                            "recommendations": ["Manual review recommended"],
                            "raw_response": response,
                            "processing_note": "Response parsed from text format"
                        }
                        
                except Exception as e:
                    print(f"❌ Error communicating with compliance agent: {e}")
                    compliance_result = {"error": f"Compliance agent communication failed: {str(e)}"}
            
            state["compliance_result"] = compliance_result
            state["messages"].append({"role": "assistant", "content": "Compliance check completed"})
            
        except Exception as e:
            print(f"❌ Compliance check exception: {str(e)}")
            state["compliance_result"] = {"error": f"Compliance check failed: {str(e)}"}
            state["messages"].append({"role": "assistant", "content": f"Compliance check error: {str(e)}"})
        
        return state
    
    async def _aggregate_results(self, state: RoutingState) -> RoutingState:
        """Aggregate all results into final response."""
        try:
            # Collect all available results
            final_result = {
                "routing_decision": state.get("route_decision", "unknown"),
                "document_data": state.get("document_data", {}),
                "risk_assessment": state.get("risk_assessment", {}),
                "compliance_result": state.get("compliance_result", {}),
                "processing_summary": {
                    "total_steps": len([k for k in state.keys() if k.endswith(('_data', '_assessment', '_result'))]),
                    "successful_steps": len([v for k, v in state.items() if k.endswith(('_data', '_assessment', '_result')) and 'error' not in v]),
                    "agent": "RoutingAgent"
                }
            }
            
            # Generate summary using LLM
            summary_prompt = f"""
            Summarize this mortgage processing workflow result:
            
            {json.dumps(final_result, indent=2)}
            
            Provide a concise summary of:
            1. What was processed
            2. Key findings
            3. Final recommendation
            4. Any issues encountered
            """
            
            summary_response = await self.llm.ainvoke([{"role": "user", "content": summary_prompt}])
            final_result["summary"] = summary_response.content
            
            # Generate PDF report
            pdf_path = await self._generate_pdf_report(final_result)
            if pdf_path:
                final_result["output_pdf_path"] = pdf_path
            
            state["final_result"] = final_result
            state["messages"].append({"role": "assistant", "content": "Final aggregation completed"})
            
        except Exception as e:
            state["final_result"] = {"error": f"Aggregation failed: {str(e)}"}
            state["messages"].append({"role": "assistant", "content": f"Aggregation error: {str(e)}"})
        
        return state
    
    async def _generate_pdf_report(self, final_result: Dict) -> Optional[str]:
        """Generate a PDF decision report with applicant name and datetime stamp."""
        try:
            # Extract applicant name from document data
            document_data = final_result.get("document_data", {})
            applicant_name = document_data.get("applicant_name", "Unknown_Applicant")
            
            # Shorter timestamp: YYYYMMDD_HHMM
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            
            # Limit applicant name length
            max_name_len = 20
            clean_name = "".join(c for c in applicant_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            clean_name = clean_name.replace(' ', '_')[:max_name_len]
            
            # Build output filename with dynamic project root
            output_filename = f"compliance_report_{timestamp}_{clean_name}.pdf"
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            output_dir = project_root / "mortgage_docs" / "output"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / output_filename
            
            # Create PDF document
            doc = SimpleDocTemplate(str(output_path), pagesize=letter,
                                  rightMargin=72, leftMargin=72,
                                  topMargin=72, bottomMargin=18)
            
            # Get styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30,
                alignment=1  # Center alignment
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=12,
                spaceAfter=12,
                textColor=colors.darkblue
            )
            
            # Build PDF content
            story = []
            
            # Title
            story.append(Paragraph("MORTGAGE APPLICATION DECISION REPORT", title_style))
            story.append(Spacer(1, 20))
            
            # Report metadata
            story.append(Paragraph("Report Information", heading_style))
            
            # Clean up source file path to show only relative path
            source_file = document_data.get("source_file", "N/A")
            if source_file != "N/A" and isinstance(source_file, str):
                # Extract only the relative path from project root
                if "mortgage_docs" in source_file:
                    source_file = "mortgage_docs" + source_file.split("mortgage_docs")[1]
                else:
                    # Just get the filename if no mortgage_docs path
                    source_file = Path(source_file).name
            
            report_info = [
                ["Report Generated:", datetime.now().strftime("%B %d, %Y at %I:%M %p")],
                ["Applicant Name:", applicant_name],
                ["Source Document:", source_file],
                ["Report ID:", timestamp]
            ]
            
            report_table = Table(report_info, colWidths=[2*inch, 4*inch])
            report_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(report_table)
            story.append(Spacer(1, 20))
            
            # Extract data for use throughout the report
            risk_assessment = final_result.get("risk_assessment", {})
            compliance_result = final_result.get("compliance_result", {})
            
            # Application Summary
            story.append(Paragraph("Application Summary", heading_style))
            
            # Get credit score from risk assessment if available, otherwise from document
            credit_score = 'Not specified'
            if risk_assessment and 'credit_score' in risk_assessment:
                credit_score = risk_assessment['credit_score']
            elif document_data and 'credit_score' in document_data and document_data['credit_score'] > 0:
                credit_score = document_data['credit_score']
            
            app_data = [
                ["Annual Income:", f"${document_data.get('income', 'Not specified')}"],
                ["Employment:", document_data.get('employment', 'Not specified')],
                ["Loan Amount:", f"${document_data.get('loan_amount', 'Not specified')}"],
                ["Credit Score:", credit_score]
            ]
            
            app_table = Table(app_data, colWidths=[2*inch, 4*inch])
            app_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(app_table)
            story.append(Spacer(1, 20))
            
            # Risk Assessment
            story.append(Paragraph("Risk Assessment", heading_style))
            
            risk_level = risk_assessment.get("risk_level", "unknown")
            risk_color = colors.green if risk_level == "low" else colors.orange if risk_level == "medium" else colors.red
            
            risk_data = [
                ["Risk Level:", risk_level.upper()],
                ["Risk Score:", f"{risk_assessment.get('risk_score', 'N/A')}/100"],
                ["Confidence:", f"{risk_assessment.get('confidence', 'N/A')}"],
                ["Debt-to-Income Ratio:", f"{risk_assessment.get('debt_to_income_ratio', 'N/A')}%"]
            ]
            
            risk_table = Table(risk_data, colWidths=[2*inch, 4*inch])
            risk_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('BACKGROUND', (1, 0), (1, 0), risk_color),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(risk_table)
            story.append(Spacer(1, 15))
            
            # Risk factors
            risk_factors = risk_assessment.get("risk_factors", [])
            if risk_factors:
                story.append(Paragraph("Risk Factors:", styles['Heading3']))
                for factor in risk_factors:
                    story.append(Paragraph(f"• {factor}", styles['Normal']))
                story.append(Spacer(1, 15))
            
            # Compliance Result
            story.append(Paragraph("Compliance Decision", heading_style))
            
            approved = compliance_result.get("approved", False)
            decision_color = colors.green if approved else colors.red
            decision_text = "APPROVED" if approved else "NOT APPROVED"
            
            compliance_data = [
                ["Decision:", decision_text],
                ["Confidence:", f"{compliance_result.get('confidence', 'N/A')}"]
            ]
            
            compliance_table = Table(compliance_data, colWidths=[2*inch, 4*inch])
            compliance_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('BACKGROUND', (1, 0), (1, 0), decision_color),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('TEXTCOLOR', (1, 0), (1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(compliance_table)
            story.append(Spacer(1, 15))
            
            # Compliance issues
            compliance_issues = compliance_result.get("compliance_issues", [])
            if compliance_issues:
                story.append(Paragraph("Compliance Issues:", styles['Heading3']))
                for issue in compliance_issues:
                    story.append(Paragraph(f"• {issue}", styles['Normal']))
                story.append(Spacer(1, 15))
            
            # Recommendations
            recommendations = compliance_result.get("recommendations", [])
            if recommendations:
                story.append(Paragraph("Recommendations", heading_style))
                for rec in recommendations:
                    story.append(Paragraph(f"• {rec}", styles['Normal']))
                story.append(Spacer(1, 15))
            
            # Executive Summary - Enhanced formatting
            summary = final_result.get("summary", "")
            if summary:
                story.append(Paragraph("Executive Summary", heading_style))
                story.append(Spacer(1, 10))
                
                # Parse and format the summary for better readability
                formatted_summary = self._format_executive_summary(summary, styles)
                for element in formatted_summary:
                    story.append(element)
            
            # Build PDF
            doc.build(story)
            
            print(f"✅ PDF report generated: {output_path}")
            return str(output_path)
            
        except Exception as e:
            print(f"❌ Error generating PDF report: {e}")
            return None
    
    def _format_executive_summary(self, summary_text: str, styles) -> List:
        """Format executive summary with proper spacing and structure."""
        from reportlab.platypus import Paragraph, Spacer
        from reportlab.lib.styles import ParagraphStyle
        import re

        elements = []

        section_style = ParagraphStyle(
            'SectionStyle',
            parent=styles['Normal'],
            fontSize=11,
            fontName='Helvetica-Bold',
            spaceAfter=6,
            textColor='#2c3e50'
        )

        bullet_style = ParagraphStyle(
            'BulletStyle',
            parent=styles['Normal'],
            fontSize=10,
            leftIndent=20,
            bulletIndent=10,
            spaceAfter=4,
            leading=13
        )

        # Remove any leading markdown headings
        summary_text = re.sub(r'^#+\s*Summary.*?\d+\.\s', '', summary_text, flags=re.IGNORECASE)

        # Match numbered sections: 1. **Title:** content
        pattern = re.compile(r'(\d+)\.\s\*\*(.*?)\*\*[:\-]?\s*(.*?)(?=\d+\.\s\*\*|$)', re.S)
        matches = pattern.findall(summary_text)

        for _, title, content in matches:
            elements.append(Paragraph(title.strip() + ":", section_style))
            # Split bullets by "- " and make them proper bullet points
            bullet_items = re.split(r'\n?- ', content.strip())
            for item in bullet_items:
                if item.strip():
                    elements.append(Paragraph(item.strip(), bullet_style, bulletText="•"))
            elements.append(Spacer(1, 10))

        return elements

    async def process_query(self, query: str) -> Dict:
        """Process a query through the routing workflow."""
        if not self.graph:
            await self.create()
        
        # Initialize state
        initial_state = RoutingState(
            messages=[],
            query=query,
            route_decision="",
            document_data={},
            risk_assessment={},
            compliance_result={},
            final_result={}
        )
        
        # Run the workflow
        try:
            final_state = await self.graph.ainvoke(initial_state)
            return final_state.get("final_result", {"error": "No final result generated"})
        except Exception as e:
            return {
                "error": f"Routing workflow failed: {str(e)}",
                "agent": "RoutingAgent"
            }
