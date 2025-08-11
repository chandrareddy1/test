import pdfplumber
import asyncio
import os
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Union, AsyncGenerator
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv

# Add project root to path for imports
import sys
from pathlib import Path

# Get the project root directory dynamically  
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

class DocumentAgent:
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]
    
    def __init__(self):
        self.agent = None
        
    async def create(self):
        """Initialize the agent with model client."""
        # Load environment variables from .env file
        load_dotenv()
        
        # Get API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        # Create the model client
        model_client = OpenAIChatCompletionClient(
            model="gpt-4o-mini",
            api_key=api_key
        )
        
        # Create the assistant agent
        self.agent = AssistantAgent(
            name="DocumentAgent",
            description="AutoGen-powered specialized agent for mortgage document analysis and data extraction",
            model_client=model_client,
            system_message="""You are a mortgage document analysis specialist. Your role is to:
            
            1. Extract key information from mortgage documents
            2. Parse applicant data including income, employment, assets
            3. Identify property details and loan information
            4. Structure data for downstream processing
            
            Focus on extracting:
            - Applicant personal information
            - Income and employment details
            - Credit history indicators
            - Property information
            - Loan amount and terms
            - Document completeness assessment
            
            Return structured data that can be used by other agents in the mortgage processing pipeline."""
        )
    
    async def process_document(self, filename: str) -> Dict:
        """Process a mortgage document and extract structured data."""
        if not self.agent:
            await self.create()
        
        try:
            # Find and read the PDF file
            pdf_path = self._find_pdf_file(filename)
            if not pdf_path:
                return {"error": f"PDF file '{filename}' not found"}
            
            # Extract text from PDF
            text_content = self._extract_pdf_text(pdf_path)
            if not text_content:
                return {"error": f"Could not extract text from '{filename}'"}
            
            # First try direct parsing with our improved regex patterns
            direct_result = self._extract_data_from_text(text_content)
            
            # If direct parsing found good data, use it
            if (direct_result.get("applicant_name") != "Not specified" or 
                direct_result.get("income", 0) > 0 or 
                direct_result.get("loan_amount", 0) > 0):
                
                # Add metadata
                direct_result.update({
                    "source_file": pdf_path,  # full path
                    "processing_timestamp": asyncio.get_running_loop().time(),
                    "agent": "DocumentAgent"
                })
                
                return direct_result
            
            # If direct parsing didn't work well, try LLM analysis
            
            # Use agent to analyze the document
            analysis_prompt = f"""
            Analyze this mortgage document and extract structured information:
            
            {text_content[:4000]}  # Limit text size for prompt
            
            Extract and return a JSON object with the following structure:
            {{
                "applicant_name": "Full name of primary applicant",
                "income": "Annual income (numeric value only)",
                "employment": "Current employment status/employer",
                "credit_score": "Credit score if mentioned",
                "loan_amount": "Requested loan amount (numeric value only)",
                "property_value": "Property value (numeric value only)",
                "down_payment": "Down payment amount (numeric value only)",
                "property_address": "Property address",
                "document_type": "Type of document (application, verification, etc.)",
                "completeness": "Assessment of document completeness",
                "extracted_data": {{
                    "monthly_income": "Monthly income",
                    "monthly_debt": "Monthly debt obligations",
                    "assets": "Total assets",
                    "employment_years": "Years with current employer"
                }}
            }}
            
            If any field is not available, use null or "Not specified".
            """
            
            from autogen_core import CancellationToken
            from autogen_agentchat.messages import TextMessage
            
            run_result = await self.agent.on_messages(
                [TextMessage(content=analysis_prompt, source="user")],
                CancellationToken()
            )
            
            response_text = ""
            if hasattr(run_result, "messages") and run_result.messages:
                last = run_result.messages[-1]
                response_text = getattr(last, "content", str(last))
            else:
                response_text = str(run_result)
            
            result = self._parse_agent_response(response_text)
            
            # Add metadata
            result.update({
                "source_file": pdf_path,  # full path
                "processing_timestamp": asyncio.get_running_loop().time(),
                "agent": "DocumentAgent"
            })
            
            return result
            
        except Exception as e:
            return {
                "error": f"Document processing failed: {str(e)}",
                "source_file": filename,
                "agent": "DocumentAgent"
            }
    
    def _find_pdf_file(self, filename: str) -> Optional[str]:
        """Find PDF file in common locations."""
        # First, check if it's already a full path that exists
        if os.path.exists(filename):
            return filename
            
        # If it's a full path but doesn't exist, extract just the filename
        base_filename = os.path.basename(filename)
        
        # Use dynamic project root for paths
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        
        search_paths = [
            f"./{base_filename}",
            project_root / "mortgage_docs" / base_filename,
            project_root / "mortgage_docs" / "input" / base_filename,
            f"./{base_filename}.pdf" if not base_filename.endswith('.pdf') else f"./{base_filename}",
        ]
        
        for path in search_paths:
            path_obj = Path(path) if isinstance(path, str) else path
            if path_obj.exists():
                return str(path_obj)
        
        return None
    
    def _extract_pdf_text(self, pdf_path: str) -> str:
        """Extract text content from PDF file."""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text_content = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content += page_text + "\n"
                return text_content.strip()
        except Exception as e:
            print(f"Error extracting PDF text: {e}")
            return ""
    
    def _parse_agent_response(self, response_text: str) -> Dict:
        """Parse agent response and extract JSON data."""
        try:
            # First try to find JSON in code fences
            fence = re.search(r"```json\s*(\{.*?\})\s*```", response_text, re.DOTALL | re.IGNORECASE)
            if fence:
                return json.loads(fence.group(1))
            
            # Then try to find any JSON object
            js = re.search(r"(\{.*?\})", response_text, re.DOTALL)
            if js:
                return json.loads(js.group(1))
            
            # Fallback: create structured data from text
            return self._extract_data_from_text(response_text)
            
        except json.JSONDecodeError:
            return self._extract_data_from_text(response_text)
        except Exception as e:
            return {
                "error": f"Response parsing failed: {e}",
                "raw_response": response_text[:500]
            }
    
    def _extract_data_from_text(self, text: str) -> Dict:
        """Fallback method to extract data from text response."""
        # Enhanced pattern matching for mortgage document fields
        result = {
            "applicant_name": self._extract_applicant_name(text),
            "income": self._extract_annual_income(text),
            "employment": self._extract_pattern(text, r"(?:Employer|Position):\s*([^\n]+)", "Not specified"),
            "credit_score": self._extract_numeric(text, r"credit\s*score[:\s]*(\d+)", 0),
            "loan_amount": self._extract_loan_amount(text),
            "property_value": self._extract_property_value(text),
            "down_payment": self._extract_numeric(text, r"down\s*payment[:\s]*\$?([0-9,]+)", 0),
            "property_address": self._extract_pattern(text, r"Property\s*Address:\s*([^\n]+)", "Not specified"),
            "document_type": "Mortgage Application",
            "completeness": "Complete extraction from structured document",
            "extracted_data": {
                "monthly_income": self._extract_monthly_income(text),
                "monthly_debt": self._calculate_monthly_debt(text),
                "assets": self._calculate_total_assets(text),
                "employment_years": self._calculate_employment_years(text)
            }
        }
        
        return result
    
    def _extract_applicant_name(self, text: str) -> str:
        """Extract applicant name with improved patterns to avoid extra text."""
        patterns = [
            r"Name:\s*([A-Za-z]+(?:\s+[A-Za-z]+)*?)(?:\s+Social|$|\n)",  # Stop at "Social" 
            r"Name:\s*([A-Za-z\s]{2,30})(?:\n|$)",  # Limit length and stop at newline
            r"Borrower.*?Name:\s*([A-Za-z\s]{2,30})(?:\n|$)",
            r"Applicant.*?Name:\s*([A-Za-z\s]{2,30})(?:\n|$)",
            r"Primary.*?Borrower:\s*([A-Za-z\s]{2,30})(?:\n|$)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Clean up the name - remove extra words
                name_words = name.split()
                if len(name_words) >= 2:
                    # Take first two words as first and last name
                    clean_name = " ".join(name_words[:2])
                    if clean_name and len(clean_name) > 2:
                        return clean_name
                elif len(name_words) == 1 and len(name_words[0]) > 1:
                    return name_words[0]
        
        return "Not specified"
    
    def _extract_annual_income(self, text: str) -> int:
        """Extract annual income from monthly income or direct annual income."""
        # Try monthly income first
        monthly_match = re.search(r"Monthly\s*Income:\s*\$?([0-9,]+)", text, re.IGNORECASE)
        if monthly_match:
            try:
                monthly = int(re.sub(r'[^\d]', '', monthly_match.group(1)))
                return monthly * 12
            except ValueError:
                pass
        
        # Try annual income
        annual_match = re.search(r"(?:Annual|Yearly)\s*Income:\s*\$?([0-9,]+)", text, re.IGNORECASE)
        if annual_match:
            try:
                return int(re.sub(r'[^\d]', '', annual_match.group(1)))
            except ValueError:
                pass
        
        return 0
    
    def _extract_loan_amount(self, text: str) -> int:
        """Extract requested loan amount."""
        patterns = [
            r"Requested\s*Loan\s*Amount:\s*\$?([0-9,]+)",
            r"Loan\s*Amount:\s*\$?([0-9,]+)",
            r"Request(?:ed)?.*?Amount:\s*\$?([0-9,]+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(re.sub(r'[^\d]', '', match.group(1)))
                except ValueError:
                    continue
        return 0
    
    def _extract_property_value(self, text: str) -> int:
        """Extract property purchase price or value."""
        patterns = [
            r"Purchase\s*Price:\s*\$?([0-9,]+)",
            r"Property\s*Value:\s*\$?([0-9,]+)",
            r"Sale\s*Price:\s*\$?([0-9,]+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(re.sub(r'[^\d]', '', match.group(1)))
                except ValueError:
                    continue
        return 0
    
    def _extract_monthly_income(self, text: str) -> int:
        """Extract monthly income."""
        match = re.search(r"Monthly\s*Income:\s*\$?([0-9,]+)", text, re.IGNORECASE)
        if match:
            try:
                return int(re.sub(r'[^\d]', '', match.group(1)))
            except ValueError:
                pass
        return 0
    
    def _calculate_monthly_debt(self, text: str) -> int:
        """Calculate total monthly debt from liabilities."""
        total_debt = 0
        debt_patterns = [
            r"Credit\s*Card\s*Debt:\s*\$?([0-9,]+)",
            r"Car\s*Loan:\s*\$?([0-9,]+)",
            r"Current\s*Mortgage:\s*\$?([0-9,]+)"
        ]
        
        for pattern in debt_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    # Assume monthly payment is roughly 3% of total debt for estimation
                    debt_amount = int(re.sub(r'[^\d]', '', match.group(1)))
                    monthly_payment = int(debt_amount * 0.03)  # Rough estimation
                    total_debt += monthly_payment
                except ValueError:
                    continue
        
        return total_debt
    
    def _calculate_total_assets(self, text: str) -> int:
        """Calculate total assets."""
        total_assets = 0
        asset_patterns = [
            r"Checking\s*Account:\s*\$?([0-9,]+)",
            r"Savings\s*Account:\s*\$?([0-9,]+)",
            r"Retirement\s*Account:\s*\$?([0-9,]+)"
        ]
        
        for pattern in asset_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    amount = int(re.sub(r'[^\d]', '', match.group(1)))
                    total_assets += amount
                except ValueError:
                    continue
        
        return total_assets
    
    def _calculate_employment_years(self, text: str) -> float:
        """Calculate years of employment from start date."""
        start_date_match = re.search(r"Start\s*Date:\s*(\d{2}/\d{2}/\d{4})", text, re.IGNORECASE)
        if start_date_match:
            try:
                from datetime import datetime
                start_date = datetime.strptime(start_date_match.group(1), "%m/%d/%Y")
                current_date = datetime.now()
                years = (current_date - start_date).days / 365.25
                return round(years, 1)
            except ValueError:
                pass
        return 0.0
    
    def _extract_pattern(self, text: str, pattern: str, default: str) -> str:
        """Extract text using regex pattern."""
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else default
    
    def _extract_numeric(self, text: str, pattern: str, default: int) -> int:
        """Extract numeric value using regex pattern."""
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return int(re.sub(r'[^\d]', '', match.group(1)))
            except ValueError:
                pass
        return default

    # PDF Discovery Methods (simplified)
    def discover_relevant_pdfs(self, query: str) -> List[str]:
        """Auto-discover relevant PDFs based on query content."""
        relevant_pdfs = []
        query_lower = query.lower()
        mortgage_keywords = ['mortgage', 'loan', 'application', 'credit', 'property', 'income']
        
        # Use dynamic project root for paths
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        
        # Search in common PDF directories
        search_dirs = [
            Path("."),
            project_root / "mortgage_docs",
            project_root / "mortgage_docs" / "input",
            Path("./documents"),
            Path("./pdfs")
        ]
        
        for search_dir in search_dirs:
            if search_dir.exists() and search_dir.is_dir():
                for pdf_file in search_dir.glob("*.pdf"):
                    if pdf_file.is_file() and os.access(pdf_file, os.R_OK):
                        pdf_name_lower = pdf_file.name.lower()
                        
                        # Direct filename match
                        if any(keyword in pdf_name_lower for keyword in mortgage_keywords):
                            relevant_pdfs.append(str(pdf_file))
                        elif any(keyword in query_lower for keyword in mortgage_keywords):
                            # If query mentions mortgage terms, include all readable PDFs
                            relevant_pdfs.append(str(pdf_file))
        
        return relevant_pdfs[:3]  # Limit to top 3 matches

    def get_available_pdfs(self) -> List[Dict[str, str]]:
        """Get list of all available PDFs with metadata"""
        pdf_list = []
        
        # Use dynamic project root for paths
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        
        # Search in common PDF directories
        search_dirs = [
            Path("."),
            project_root / "mortgage_docs",
            project_root / "mortgage_docs" / "input",
            Path("./documents"),
            Path("./pdfs")
        ]
        
        for search_dir in search_dirs:
            if search_dir.exists() and search_dir.is_dir():
                for pdf_file in search_dir.glob("*.pdf"):
                    if pdf_file.is_file():
                        try:
                            size = pdf_file.stat().st_size
                            is_readable = os.access(pdf_file, os.R_OK)
                            
                            pdf_list.append({
                                "path": str(pdf_file),
                                "name": pdf_file.name,
                                "size": f"{size/1024:.1f} KB",
                                "readable": is_readable,
                                "directory": str(pdf_file.parent)
                            })
                        except (OSError, PermissionError):
                            continue
        
        return pdf_list

    async def invoke(self, query: str, context_id: str = None, pdf_selection_mode: str = "auto") -> AsyncGenerator[Dict, None]:
        """Main invoke method for A2A integration."""
        if not self.agent:
            await self.create()
        
        try:
            # Determine which PDFs to process
            pdfs_to_process = []
            
            if pdf_selection_mode == "auto":
                pdfs_to_process = self.discover_relevant_pdfs(query)
            elif pdf_selection_mode == "all":
                available_pdfs = self.get_available_pdfs()
                pdfs_to_process = [pdf["path"] for pdf in available_pdfs if pdf["readable"]]
            elif pdf_selection_mode == "explicit":
                # Extract filename from query
                pdf_files = re.findall(r'(\w+\.pdf)', query, re.IGNORECASE)
                for filename in pdf_files:
                    pdf_path = self._find_pdf_file(filename)
                    if pdf_path:
                        pdfs_to_process.append(pdf_path)
            
            if not pdfs_to_process:
                yield {
                    "is_task_complete": True,
                    "content": "No relevant PDF documents found for processing.",
                    "updates": "Document search completed - no files matched criteria"
                }
                return
            
            # Process each PDF
            all_results = []
            for i, pdf_path in enumerate(pdfs_to_process):
                filename = Path(pdf_path).name
                
                yield {
                    "is_task_complete": False,
                    "updates": f"Processing document {i+1}/{len(pdfs_to_process)}: {filename}"
                }
                
                result = await self.process_document(filename)
                all_results.append(result)
                
                yield {
                    "is_task_complete": False,
                    "updates": f"Completed analysis of {filename}"
                }
            
            # Final result
            final_content = {
                "processed_documents": len(all_results),
                "results": all_results,
                "query": query,
                "processing_mode": pdf_selection_mode
            }
            
            yield {
                "is_task_complete": True,
                "content": json.dumps(final_content, indent=2),
                "updates": f"Document processing complete - analyzed {len(all_results)} files"
            }
            
        except Exception as e:
            yield {
                "is_task_complete": True,
                "content": f"Document processing failed: {str(e)}",
                "updates": "Error occurred during document processing"
            }
