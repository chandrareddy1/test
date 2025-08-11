import asyncio
import os
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Union
from smolagents import CodeAgent, OpenAIModel
from dotenv import load_dotenv

# Add project root to path for imports
import sys

# Get the project root directory dynamically
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from utilities.mcp.tools.mcp_credit_tools import MockCreditAPITool, VertexAIRiskTool

class CreditRiskAgent:
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain", "application/json"]

    def __init__(self):
        self.agent = None
        # Initialize MCP credit tools
        self.credit_api_tool = MockCreditAPITool()
        self.vertex_ai_tool = VertexAIRiskTool()

    async def create(self):
        """Initialize the agent with SmoIAgents."""
        # Load environment variables from .env file
        load_dotenv()

        # Get API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        # Create the OpenAI model
        model = OpenAIModel(model_id="gpt-4o-mini", api_key=api_key)

        # Create the SmoIAgents agent with OpenAI
        self.agent = CodeAgent(
            tools=[],  # Add tools as needed
            model=model,
            additional_authorized_imports=['json', 're', 'math', 'statistics']
        )

    async def process_document_data(self, doc_data: Dict) -> Dict:
        """Process document data and perform credit risk assessment using MCP tools."""
        if not self.agent:
            await self.create()

        try:
            print(f"[CreditRiskAgent] Processing document data: {doc_data}")
            
            # Extract applicant info for credit lookup
            applicant_name = doc_data.get("applicant_name", "Unknown")
            annual_income = doc_data.get("income", 0)
            loan_amount = doc_data.get("loan_amount", 0)
            property_value = doc_data.get("property_value", 0)
            
            print(f"[CreditRiskAgent] Extracted - Name: {applicant_name}, Income: {annual_income}, Loan: {loan_amount}")
            
            # Get credit score using MCP credit API tool
            print(f"[CreditRiskAgent] Getting credit score for {applicant_name} using MCP tools...")
            credit_data = await self.credit_api_tool.get_credit_score(applicant_name)
            credit_score = credit_data.get("credit_score", 720)
            print(f"[CreditRiskAgent] MCP Credit API returned: {credit_data}")
            print(f"[CreditRiskAgent] Extracted credit score: {credit_score}")
            
            # Calculate financial ratios
            monthly_income = annual_income / 12 if annual_income > 0 else 0
            monthly_debt = doc_data.get("extracted_data", {}).get("monthly_debt", 0)
            dti_ratio = (monthly_debt / monthly_income * 100) if monthly_income > 0 else 0
            ltv_ratio = (loan_amount / property_value * 100) if property_value > 0 else 80
            
            # Prepare financial data for AI risk assessment
            financial_data = {
                "credit_score": credit_score,
                "dti_ratio": dti_ratio,
                "ltv_ratio": ltv_ratio,
                "annual_income": annual_income
            }
            
            print(f"[CreditRiskAgent] Prepared financial data for AI: {financial_data}")
            
            # Use MCP Vertex AI tool for risk prediction
            print(f"[CreditRiskAgent] Running AI risk assessment with financial data...")
            risk_assessment = await self.vertex_ai_tool.predict_default_risk(financial_data)
            print(f"[CreditRiskAgent] MCP Vertex AI returned: {risk_assessment}")
            
            # Combine credit data and risk assessment
            result = {
                "applicant_name": applicant_name,
                "credit_score": credit_score,
                "credit_history": credit_data.get("credit_history", {}),
                "risk_level": risk_assessment.get("risk_level", "medium"),
                "risk_score": risk_assessment.get("risk_score", 50),
                "confidence": risk_assessment.get("confidence", 0.8),
                "debt_to_income_ratio": dti_ratio,
                "loan_to_value_ratio": ltv_ratio,
                "annual_income": annual_income,
                "monthly_debt": monthly_debt,
                "risk_factors": risk_assessment.get("risk_factors", []),
                "recommendations": risk_assessment.get("recommendations", []),
                "metrics": {
                    "credit_score": credit_score,
                    "dti_ratio": dti_ratio,
                    "ltv_ratio": ltv_ratio,
                    "monthly_income": monthly_income,
                    "monthly_debt": monthly_debt
                },
                "agent": "CreditRiskAgent",
                "mcp_tools_used": ["MockCreditAPITool", "VertexAIRiskTool"]
            }
            
            print(f"[CreditRiskAgent] Final result: {result}")
            return result

        except Exception as e:
            print(f"[CreditRiskAgent] MCP credit assessment failed: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to manual assessment if MCP tools fail
            return await self._assess_credit_risk_manual(doc_data)
    
    async def _assess_credit_risk_manual(self, doc_data: Dict) -> Dict:
        """Manual fallback credit risk assessment."""
        try:
            financial_data = self._extract_financial_metrics(doc_data)
            return await self._assess_credit_risk(financial_data)
        except Exception as e:
            return {
                "risk_level": "high",
                "risk_score": 0,
                "confidence": 0.0,
                "credit_score_estimate": 0,
                "debt_to_income_ratio": 0,
                "annual_income": 0,
                "monthly_debt": 0,
                "risk_factors": [f"Processing error: {str(e)}"],
                "recommendations": ["Manual review required due to processing error"],
                "metrics": {},
                "agent": "CreditRiskAgent"
            }

    def _extract_financial_metrics(self, doc_data: Union[Dict, str]) -> Dict:
        """Extract key financial metrics from document data."""
        # Handle both string and dict inputs
        if isinstance(doc_data, str):
            try:
                doc_data = json.loads(doc_data)
            except json.JSONDecodeError:
                return self._extract_from_text(doc_data)

        # Extract financial information
        annual_income = 0
        monthly_debt = 0
        credit_score = 0

        # Try different possible field names for income
        income_fields = ['annual_income', 'income', 'yearly_income', 'gross_income']
        for field in income_fields:
            if field in doc_data:
                try:
                    annual_income = float(doc_data[field])
                    break
                except (ValueError, TypeError):
                    continue

        # Try different possible field names for debt
        debt_fields = ['monthly_debt', 'debt', 'monthly_payments', 'total_debt']
        for field in debt_fields:
            if field in doc_data:
                try:
                    monthly_debt = float(doc_data[field])
                    break
                except (ValueError, TypeError):
                    continue

        # Try different possible field names for credit score
        credit_fields = ['credit_score', 'fico_score', 'credit_rating']
        for field in credit_fields:
            if field in doc_data:
                try:
                    credit_score = float(doc_data[field])
                    break
                except (ValueError, TypeError):
                    continue

        return {
            "annual_income": annual_income,
            "monthly_debt": monthly_debt,
            "credit_score": credit_score,
            "employment_history": doc_data.get("employment_history", ""),
            "applicant_name": doc_data.get("applicant_name", "Unknown"),
            "loan_amount": doc_data.get("loan_amount", 0)
        }

    def _extract_from_text(self, text: str) -> Dict:
        """Extract financial data from text using simple parsing."""
        # Simple regex patterns to extract financial data
        income_match = re.search(r'income[:\s]*\$?([0-9,]+)', text, re.IGNORECASE)
        debt_match = re.search(r'debt[:\s]*\$?([0-9,]+)', text, re.IGNORECASE)
        credit_match = re.search(r'credit[_\s]*score[:\s]*([0-9]+)', text, re.IGNORECASE)

        annual_income = 0
        if income_match:
            try:
                annual_income = float(income_match.group(1).replace(',', ''))
            except:
                pass

        monthly_debt = 0
        if debt_match:
            try:
                monthly_debt = float(debt_match.group(1).replace(',', ''))
            except:
                pass

        credit_score = 0
        if credit_match:
            try:
                credit_score = float(credit_match.group(1))
            except:
                pass

        return {
            "annual_income": annual_income,
            "monthly_debt": monthly_debt,
            "credit_score": credit_score,
            "employment_history": "",
            "applicant_name": "Unknown",
            "loan_amount": 0
        }

    async def _assess_credit_risk(self, financial_data: Dict) -> Dict:
        """Perform detailed credit risk assessment."""
        annual_income = financial_data.get("annual_income", 0)
        monthly_debt = financial_data.get("monthly_debt", 0)
        credit_score = financial_data.get("credit_score", 0)
        loan_amount = financial_data.get("loan_amount", 0)

        # Calculate debt-to-income ratio
        monthly_income = annual_income / 12 if annual_income > 0 else 0
        debt_to_income = (monthly_debt / monthly_income * 100) if monthly_income > 0 else 100

        # Assess risk factors
        risk_factors = []
        risk_score = 0

        # Credit score assessment
        if credit_score == 0:
            risk_factors.append("No credit score provided")
            risk_score += 30
        elif credit_score < 580:
            risk_factors.append("Poor credit score (below 580)")
            risk_score += 40
        elif credit_score < 620:
            risk_factors.append("Fair credit score (580-619)")
            risk_score += 25
        elif credit_score < 670:
            risk_factors.append("Good credit score (620-669)")
            risk_score += 10
        elif credit_score < 740:
            risk_score += 5  # Very good credit
        # Excellent credit (740+) adds no risk

        # Debt-to-income assessment
        if debt_to_income > 43:
            risk_factors.append(f"High debt-to-income ratio ({debt_to_income:.1f}%)")
            risk_score += 25
        elif debt_to_income > 36:
            risk_factors.append(f"Elevated debt-to-income ratio ({debt_to_income:.1f}%)")
            risk_score += 15

        # Income assessment
        if annual_income < 30000:
            risk_factors.append("Low annual income (below $30,000)")
            risk_score += 20
        elif annual_income < 50000:
            risk_factors.append("Moderate annual income ($30,000-$49,999)")
            risk_score += 10

        # Determine risk level
        if risk_score >= 50:
            risk_level = "high"
        elif risk_score >= 25:
            risk_level = "medium"
        else:
            risk_level = "low"

        # Generate recommendations
        recommendations = []
        if credit_score < 620:
            recommendations.append("Consider credit improvement strategies before application")
        if debt_to_income > 43:
            recommendations.append("Reduce monthly debt obligations to improve DTI ratio")
        if annual_income < 50000:
            recommendations.append("Consider co-signer or additional income sources")
        if not recommendations:
            recommendations.append("Applicant meets basic credit criteria")

        # Calculate confidence based on available data
        confidence = 0.7
        if credit_score > 0:
            confidence += 0.2
        if annual_income > 0:
            confidence += 0.1

        return {
            "risk_level": risk_level,
            "risk_score": min(risk_score, 100),  # Cap risk score at 100
            "confidence": min(confidence, 1.0),
            "credit_score_estimate": credit_score,
            "debt_to_income_ratio": round(debt_to_income, 2),
            "annual_income": annual_income,
            "monthly_debt": monthly_debt,
            "risk_factors": risk_factors,
            "recommendations": recommendations,
            "metrics": {
                "debt_to_income_ratio": round(debt_to_income, 2),
                "credit_score": credit_score,
                "annual_income": annual_income,
                "monthly_debt": monthly_debt,
                "loan_amount": loan_amount
            },
            "agent": "CreditRiskAgent"
        }