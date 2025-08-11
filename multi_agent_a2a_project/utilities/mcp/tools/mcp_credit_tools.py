"""
MCP (Model Context Protocol) Credit Tools
Mock credit APIs and Vertex AI integration for credit risk assessment.
"""

import asyncio
import json
import random
from typing import Dict, Any, Optional
from smolagents import Tool
import os
from dotenv import load_dotenv


class MockCreditAPITool(Tool):
    """Mock Credit API tool for simulating credit bureau calls."""
    
    name = "mock_credit_api"
    description = "Simulates credit bureau API calls to get credit scores and history"
    inputs = {
        "applicant_name": {
            "type": "string", 
            "description": "Full name of the loan applicant"
        }
    }
    output_type = "string"
    
    def __init__(self):
        super().__init__()
        load_dotenv()
    
    async def get_credit_score(self, applicant_name: str) -> Dict[str, Any]:
        """
        Simulate credit bureau API call.
        In production, this would integrate with Experian, Equifax, etc.
        """
        
        # Simulate API delay
        await asyncio.sleep(0.5)
        
        # Generate realistic but deterministic credit data based on name
        name_hash = hash(applicant_name.lower()) % 1000
        
        # Base credit score (580-850 range)
        base_score = 580 + (name_hash % 270)
        
        # Adjust for common names to create realistic scenarios
        if "john" in applicant_name.lower():
            base_score = max(720, base_score)  # John tends to have good credit
        elif "jane" in applicant_name.lower():
            base_score = max(680, base_score)
        
        # Generate related credit metrics
        credit_data = {
            "credit_score": base_score,
            "credit_score_range": self._get_score_range(base_score),
            "credit_history_length": f"{max(1, (name_hash % 15))} years",
            "payment_history": self._get_payment_history(base_score),
            "credit_utilization": f"{max(5, (name_hash % 45))}%",
            "total_accounts": max(3, (name_hash % 20)),
            "open_accounts": max(2, (name_hash % 12)),
            "recent_inquiries": name_hash % 5,
            "derogatory_marks": max(0, (name_hash % 4) - 2),
            "api_provider": "MockCreditBureau",
            "timestamp": asyncio.get_event_loop().time()
        }
        
        return credit_data
    
    def _get_score_range(self, score: int) -> str:
        """Get credit score range category."""
        if score >= 800:
            return "Excellent (800-850)"
        elif score >= 740:
            return "Very Good (740-799)"
        elif score >= 670:
            return "Good (670-739)"
        elif score >= 580:
            return "Fair (580-669)"
        else:
            return "Poor (300-579)"
    
    def _get_payment_history(self, score: int) -> str:
        """Get payment history description based on score."""
        if score >= 750:
            return "Excellent - No late payments"
        elif score >= 700:
            return "Good - 1-2 late payments in last 2 years"
        elif score >= 650:
            return "Fair - Some late payments"
        else:
            return "Poor - Multiple late payments or defaults"
    
    async def forward(self, applicant_name: str) -> str:
        """Tool interface for smolagents."""
        try:
            result = await self.get_credit_score(applicant_name)
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Credit API Error: {str(e)}"


class VertexAIRiskTool(Tool):
    """Vertex AI integration for advanced risk modeling."""
    
    name = "vertex_ai_risk_model"
    description = "Uses Vertex AI models to perform advanced credit risk predictions"
    inputs = {
        "financial_data": {
            "type": "object",
            "description": "Financial data for risk assessment",
            "properties": {
                "credit_score": {"type": "number"},
                "dti_ratio": {"type": "number"},
                "ltv_ratio": {"type": "number"},
                "annual_income": {"type": "number"}
            }
        }
    }
    output_type = "string"
    
    def __init__(self):
        super().__init__()
        load_dotenv()
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT_ID', 'mock-project')
        self.model_name = "credit-risk-model-v1"
    
    async def predict_default_risk(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate Vertex AI model prediction for default risk.
        In production, this would call actual Vertex AI endpoints.
        """
        
        # Simulate model processing time
        await asyncio.sleep(1.0)
        
        # Extract features for risk modeling
        credit_score = financial_data.get('credit_score', 700)
        dti_ratio = financial_data.get('dti_ratio', 30)
        ltv_ratio = financial_data.get('ltv_ratio', 80)
        income = financial_data.get('annual_income', 50000)
        
        # Simulate ML model scoring
        risk_score = self._calculate_ml_risk_score(credit_score, dti_ratio, ltv_ratio, income)
        
        # Generate model output
        prediction_result = {
            "default_probability": risk_score,
            "risk_category": self._get_risk_category(risk_score),
            "feature_importance": {
                "credit_score": 0.35,
                "dti_ratio": 0.30,
                "ltv_ratio": 0.20,
                "income_level": 0.15
            },
            "model_confidence": min(0.95, max(0.60, 0.85 + random.uniform(-0.15, 0.15))),
            "model_version": self.model_name,
            "prediction_timestamp": asyncio.get_event_loop().time(),
            "shap_values": self._generate_shap_values(credit_score, dti_ratio, ltv_ratio, income)
        }
        
        return prediction_result
    
    def _calculate_ml_risk_score(self, credit_score: int, dti: float, ltv: float, income: float) -> float:
        """Simulate ML model risk scoring."""
        
        # Normalize inputs
        credit_normalized = (credit_score - 300) / 550  # 300-850 range
        dti_risk = min(dti / 60, 1.0)  # DTI risk increases with ratio
        ltv_risk = min(ltv / 100, 1.0)  # LTV risk
        income_factor = max(0, min(1.0, (100000 - income) / 80000))  # Higher income = lower risk
        
        # Weighted risk calculation (simulate ML model)
        base_risk = (
            (1 - credit_normalized) * 0.35 +  # Lower credit = higher risk
            dti_risk * 0.30 +                  # Higher DTI = higher risk
            ltv_risk * 0.20 +                  # Higher LTV = higher risk
            income_factor * 0.15               # Lower income = higher risk
        )
        
        # Add some randomness to simulate model uncertainty
        noise = random.uniform(-0.05, 0.05)
        risk_score = max(0.01, min(0.99, base_risk + noise))
        
        return round(risk_score, 4)
    
    def _get_risk_category(self, risk_score: float) -> str:
        """Convert risk score to category."""
        if risk_score < 0.1:
            return "Very Low Risk"
        elif risk_score < 0.25:
            return "Low Risk"
        elif risk_score < 0.50:
            return "Medium Risk"
        elif risk_score < 0.75:
            return "High Risk"
        else:
            return "Very High Risk"
    
    def _generate_shap_values(self, credit_score: int, dti: float, ltv: float, income: float) -> Dict[str, float]:
        """Generate mock SHAP values for model explainability."""
        return {
            "credit_score_impact": -0.15 if credit_score > 700 else 0.20,
            "dti_impact": 0.10 if dti > 40 else -0.05,
            "ltv_impact": 0.08 if ltv > 85 else -0.03,
            "income_impact": -0.12 if income > 75000 else 0.08
        }
    
    async def forward(self, financial_data: dict) -> str:
        """Tool interface for smolagents."""
        try:
            result = await self.predict_default_risk(financial_data)
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Vertex AI Risk Model Error: {str(e)}"


class MCPCreditBroker:
    """
    MCP (Model Context Protocol) broker for credit services.
    Orchestrates multiple credit data sources and AI models.
    """
    
    def __init__(self):
        self.credit_api = MockCreditAPITool()
        self.vertex_ai = VertexAIRiskTool()
        self.enabled_services = ["mock_credit", "vertex_ai"]
    
    async def get_comprehensive_credit_assessment(self, applicant_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive credit assessment using all available MCP services."""
        
        applicant_name = applicant_data.get('applicant_name', 'Unknown')
        
        # Parallel execution of credit services
        tasks = []
        
        if "mock_credit" in self.enabled_services:
            tasks.append(self.credit_api.get_credit_score(applicant_name))
        
        if "vertex_ai" in self.enabled_services:
            # Prepare financial data for Vertex AI
            financial_data = {
                "credit_score": applicant_data.get('credit_score', 700),
                "dti_ratio": applicant_data.get('dti_ratio', 30),
                "ltv_ratio": applicant_data.get('ltv_ratio', 80),
                "annual_income": applicant_data.get('annual_income', 50000)
            }
            tasks.append(self.vertex_ai.predict_default_risk(financial_data))
        
        # Execute all services
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Compile comprehensive assessment
        assessment = {
            "applicant_name": applicant_name,
            "services_used": self.enabled_services,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Add results from each service
        for i, service in enumerate(self.enabled_services):
            if i < len(results) and not isinstance(results[i], Exception):
                assessment[f"{service}_data"] = results[i]
            else:
                assessment[f"{service}_error"] = str(results[i]) if i < len(results) else "Service not available"
        
        return assessment
