import asyncio
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Union
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

class ComplianceAgent:
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]
    
    def __init__(self):
        self.agent = None
        self.crew = None
        
    async def create(self):
        """Initialize the agent with CrewAI."""
        # Load environment variables from .env file
        load_dotenv()
        
        # Get API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        # Create the LLM
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=api_key
        )
        
        # Create the CrewAI agent
        self.agent = Agent(
            role="Mortgage Compliance Specialist",
            goal="Analyze mortgage applications for regulatory compliance and risk factors",
            backstory="""You are an expert mortgage compliance specialist with years of experience 
            in regulatory requirements, lending standards, and risk assessment. You ensure all 
            mortgage applications meet federal and state compliance requirements including 
            Truth in Lending Act, Fair Housing Act, and other regulatory standards.""",
            llm=llm,
            verbose=True,
            allow_delegation=False
        )
    
    async def process(self, content: str, content_type: str = "text/plain") -> Dict:
        """Process content and return compliance analysis."""
        if not self.agent:
            await self.create()
        
        try:
            # Parse the content as JSON if it's structured data
            if content.strip().startswith('{'):
                data = json.loads(content)
                return await self._analyze_structured_data(data)
            else:
                # Process as text content using CrewAI
                return await self._analyze_with_crewai(content)
                
        except json.JSONDecodeError:
            # Treat as plain text
            return await self._analyze_with_crewai(content)
    
    async def _analyze_with_crewai(self, content: str) -> Dict:
        """Analyze content using CrewAI framework."""
        # Create a compliance analysis task
        task = Task(
            description=f"""
            Analyze the following mortgage-related content for compliance issues:
            
            {content}
            
            Provide a comprehensive compliance analysis including:
            1. Overall approval recommendation (approved/denied)
            2. Confidence level (0-1)
            3. List of compliance issues identified
            4. List of actionable recommendations
            5. Brief summary of the analysis
            
            Focus on mortgage lending compliance, risk factors, and regulatory requirements
            including Truth in Lending Act, Fair Housing Act, and other applicable regulations.
            
            Return the response in JSON format with these exact keys:
            - approved (boolean)
            - confidence (number 0-1)
            - compliance_issues (array of strings)
            - recommendations (array of strings)
            - summary (string)
            """,
            agent=self.agent,
            expected_output="JSON formatted compliance analysis report"
        )
        
        # Create crew and execute task
        crew = Crew(
            agents=[self.agent],
            tasks=[task],
            verbose=True
        )
        
        try:
            # Execute the crew task
            result = crew.kickoff()
            
            # Try to parse JSON from result
            result_text = str(result)
            import re
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                parsed_result = json.loads(json_match.group())
                parsed_result["agent"] = "ComplianceAgent"
                return parsed_result
            
            # Fallback response if JSON parsing fails
            return {
                "approved": False,
                "confidence": 0.5,
                "compliance_issues": ["Unable to parse compliance analysis"],
                "recommendations": ["Manual review recommended"],
                "summary": "Analysis completed but response format needs review",
                "agent": "ComplianceAgent"
            }
            
        except Exception as e:
            return {
                "approved": False,
                "confidence": 0.0,
                "compliance_issues": [f"CrewAI processing error: {str(e)}"],
                "recommendations": ["Manual review required"],
                "summary": "Technical error during compliance analysis",
                "agent": "ComplianceAgent"
            }
    
    async def _analyze_structured_data(self, data: Dict) -> Dict:
        """Analyze structured mortgage application data."""
        # Extract key metrics from potentially nested structure
        # Check if we have nested data from routing agent
        if "risk_assessment" in data and "document_data" in data:
            # Extract from nested structure sent by routing agent
            risk_data = data.get("risk_assessment", {})
            doc_data = data.get("document_data", {})
            
            credit_score = risk_data.get('credit_score', doc_data.get('credit_score', 0))
            annual_income = risk_data.get('annual_income', doc_data.get('income', 0))
            monthly_debt = risk_data.get('monthly_debt', 0)
            loan_amount = doc_data.get('loan_amount', 0)
            
            # Use calculated DTI from risk assessment if available
            debt_to_income = risk_data.get('debt_to_income_ratio', 0)
        else:
            # Direct structure - extract from top level
            credit_score = data.get('credit_score', 0)
            annual_income = data.get('annual_income', data.get('income', 0))
            monthly_debt = data.get('monthly_debt', 0)
            loan_amount = data.get('loan_amount', 0)
            
            # Calculate debt-to-income ratio
            monthly_income = annual_income / 12 if annual_income > 0 else 0
            debt_to_income = (monthly_debt / monthly_income * 100) if monthly_income > 0 else 0
        
        # Perform compliance checks
        compliance_issues = []
        recommendations = []
        
        # Credit score check
        if credit_score < 620:
            compliance_issues.append("Credit score below conventional lending minimum (620)")
            recommendations.append("Consider FHA loan options or credit improvement strategies")
        elif credit_score < 740:
            recommendations.append("Credit score could be improved for better rates")
        
        # Debt-to-income check
        if debt_to_income > 43:
            compliance_issues.append(f"Debt-to-income ratio ({debt_to_income:.1f}%) exceeds recommended maximum (43%)")
            recommendations.append("Consider debt reduction or lower loan amount")
        elif debt_to_income > 36:
            recommendations.append("DTI ratio is acceptable but on the higher side")
        
        # Income verification
        if annual_income < 30000:
            compliance_issues.append("Annual income may be insufficient for mortgage qualification")
            recommendations.append("Verify income documentation and consider co-signer")
        
        # Determine overall approval status
        approved = len(compliance_issues) == 0 and credit_score >= 620 and debt_to_income <= 43
        
        return {
            "approved": approved,
            "confidence": 0.85 if approved else 0.65,
            "compliance_issues": compliance_issues,
            "recommendations": recommendations,
            "metrics": {
                "credit_score": credit_score,
                "debt_to_income_ratio": round(debt_to_income, 2),
                "annual_income": annual_income,
                "monthly_debt": monthly_debt,
                "loan_amount": loan_amount
            },
            "agent": "ComplianceAgent"
        }
