#!/usr/bin/env python3
"""
Credit Services MCP Server
Exposes credit API and risk assessment tools via Model Context Protocol
"""

from mcp.server.fastmcp import FastMCP
import asyncio
import json
import logging
import sys
import os

# Add project root to path for imports
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from utilities.mcp.tools.mcp_credit_tools import MockCreditAPITool, VertexAIRiskTool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("credit-mcp-server")

# Initialize FastMCP server
mcp = FastMCP("credit_api_server")

# Initialize credit tools
credit_api = MockCreditAPITool()
vertex_ai = VertexAIRiskTool()

@mcp.tool("get_credit_score")
async def get_credit_score(applicant_name: str) -> str:
    """
    Get credit score and history from credit bureau API

    Args:
        applicant_name (str): Full name of the loan applicant

    Returns:
        str: JSON string containing credit score and related data
    """
    try:
        logger.info(f"Getting credit score for: {applicant_name}")
        result = await credit_api.get_credit_score(applicant_name)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Credit score lookup failed: {e}")
        return json.dumps({"error": f"Credit score lookup failed: {str(e)}"})

@mcp.tool("predict_default_risk")
async def predict_default_risk(financial_data: dict) -> str:
    """
    Use AI model to predict default risk based on financial data

    Args:
        financial_data (dict): Dictionary containing credit_score, dti_ratio, ltv_ratio, annual_income

    Returns:
        str: JSON string containing risk assessment data
    """
    try:
        logger.info(f"Predicting default risk for: {financial_data}")
        result = await vertex_ai.predict_default_risk(financial_data)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Risk prediction failed: {e}")
        return json.dumps({"error": f"Risk prediction failed: {str(e)}"})

@mcp.tool("comprehensive_credit_assessment")
async def comprehensive_credit_assessment(applicant_data: dict) -> str:
    """
    Get comprehensive credit assessment using all available services

    Args:
        applicant_data (dict): Dictionary containing applicant information

    Returns:
        str: JSON string containing comprehensive assessment data
    """
    try:
        applicant_name = applicant_data.get("applicant_name", "Unknown")
        credit_score = applicant_data.get("credit_score")
        dti_ratio = applicant_data.get("dti_ratio", 30.0)
        ltv_ratio = applicant_data.get("ltv_ratio", 80.0)
        annual_income = applicant_data.get("annual_income", 50000.0)
        
        logger.info(f"Running comprehensive assessment for: {applicant_name}")
        
        # Get credit score if not provided
        if credit_score is None:
            credit_data = await credit_api.get_credit_score(applicant_name)
            actual_credit_score = credit_data.get("credit_score", 720)
        else:
            credit_data = await credit_api.get_credit_score(applicant_name)
            actual_credit_score = credit_score
        
        # Prepare financial data for AI assessment
        financial_data = {
            "credit_score": actual_credit_score,
            "dti_ratio": dti_ratio,
            "ltv_ratio": ltv_ratio,
            "annual_income": annual_income
        }
        
        # Get AI risk assessment
        risk_assessment = await vertex_ai.predict_default_risk(financial_data)
        
        # Combine results
        comprehensive_result = {
            "applicant_name": applicant_name,
            "credit_data": credit_data,
            "risk_assessment": risk_assessment,
            "financial_metrics": financial_data,
            "timestamp": asyncio.get_event_loop().time(),
            "mcp_server": "credit-api-server",
            "service_version": "1.0.0"
        }
        
        return json.dumps(comprehensive_result, indent=2)
        
    except Exception as e:
        logger.error(f"Comprehensive assessment failed: {e}")
        return json.dumps({"error": f"Assessment failed: {str(e)}"})

if __name__ == "__main__":
    logger.info("Starting Credit MCP Server...")
    print("Credit MCP Server is ready to accept requests")
    print("Available tools: get_credit_score, predict_default_risk, comprehensive_credit_assessment")
    mcp.run(transport="stdio")
