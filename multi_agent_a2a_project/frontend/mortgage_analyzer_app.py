#!/usr/bin/env python3
"""
MortgageInsight Pro - AI-Powered Mortgage Analysis Platform
Professional mortgage application processing with multi-agent AI analysis.
Streamlit Frontend for comprehensive document analysis, risk assessment, and compliance checking.
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
import streamlit as st
import sys

# ---- Path setup (project root first) ------------------------------------------------------------
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from utilities.a2a.agent_connect import AgentConnector
from utilities.a2a.agent_discovery import AgentDiscovery
from a2a.types import AgentCard

# ---- Page configuration (must be FIRST Streamlit call) ------------------------------------------
st.set_page_config(
    page_title="MortgageInsight Pro - AI Analysis Platform",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---- Custom CSS ---------------------------------------------------------------------------------
st.markdown(
    """
<style>
    /* Slightly increase top spacing to prevent header clipping */
    .main > div {
        padding-top: 2.5rem !important;
    }
    .block-container {
        padding-top: 2rem !important;
        margin-top: 0rem !important;
    }
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f4e79;
        text-align: center;
        margin-bottom: 1rem;
        margin-top: 0.5rem;
        padding-top: 0.5rem;
    }
    h1 {
        margin-top: 0.5rem !important;
        padding-top: 0.5rem !important;
    }
    .success-box, .error-box, .info-box {
        padding: 1rem; border-radius: 0.5rem; margin: 1rem 0;
    }
    .success-box { background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724; }
    .error-box   { background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
    .info-box    { background-color: #d1ecf1; border: 1px solid #bee5eb; color: #0c5460; }
    .metric-card {
        background-color: #f8f9fa; padding: 1rem; border-radius: 0.5rem;
        border: 1px solid #dee2e6; margin: 0.5rem 0;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ---- App core -----------------------------------------------------------------------------------
class MortgageProcessorApp:
    def __init__(self):
        self.discovery = AgentDiscovery()
        self.available_agents: Dict[str, AgentCard] = {}
        self.processing_complete = False

    def discover_agents_sync(self) -> bool:
        """Synchronous wrapper for discovering agents."""
        async def _discover():
            try:
                self.available_agents = await self.discovery.discover_agents()
                return True
            except Exception as e:
                st.error(f"Failed to discover agents: {e}")
                return False

        try:
            loop = asyncio.new_event_loop()
            try:
                asyncio.set_event_loop(loop)
                return loop.run_until_complete(_discover())
            finally:
                loop.close()
        except Exception as e:
            st.error(f"Failed to run async discovery: {e}")
            return False

    def find_routing_agent(self) -> Optional[AgentCard]:
        """Find the routing agent from discovered agents."""
        for name, card in self.available_agents.items():
            if "routing" in name.lower() or "router" in name.lower():
                return card
        return None

    def process_mortgage_application_sync(self, pdf_file, uploaded_filename: str) -> Dict[str, Any]:
        """Synchronous wrapper for processing mortgage application."""
        async def _process():
            try:
                # Save uploaded file to temporary location
                temp_dir = Path("temp_uploads")
                temp_dir.mkdir(exist_ok=True)

                temp_file_path = temp_dir / uploaded_filename
                with open(temp_file_path, "wb") as f:
                    f.write(pdf_file.getvalue())

                # Find routing agent
                routing_agent = self.find_routing_agent()
                if not routing_agent:
                    return {"error": "Routing agent not found. Please ensure all agents are running."}

                # Connect to routing agent
                connector = AgentConnector(routing_agent)

                # Create query for processing
                query = f"I need to process a mortgage application. I have a PDF file at {temp_file_path}"

                # Generate session ID
                import uuid
                session_id = str(uuid.uuid4())

                # Send request to routing agent
                response = await connector.send_task(query, session_id)

                # Parse response
                try:
                    result = json.loads(response)
                    # Clean up temp file
                    try:
                        temp_file_path.unlink(missing_ok=True)
                    except Exception:
                        pass
                    return result
                except json.JSONDecodeError:
                    return {"error": f"Invalid response format from routing agent: {response}"}

            except Exception as e:
                return {"error": f"Processing failed: {e}"}

        try:
            loop = asyncio.new_event_loop()
            try:
                asyncio.set_event_loop(loop)
                return loop.run_until_complete(_process())
            finally:
                loop.close()
        except Exception as e:
            return {"error": f"Failed to run async processing: {e}"}

# ---- UI helpers ---------------------------------------------------------------------------------
def display_agent_status(available_agents: Dict[str, AgentCard]) -> bool:
    """Display the status of discovered agents."""
    st.sidebar.markdown("## 🤖 Agent Status")

    if not available_agents:
        st.sidebar.error("❌ No agents discovered")
        st.sidebar.markdown("Please ensure all agents are running:")
        st.sidebar.code(
            """
# Using the scripts folder (recommended)
./scripts/start-all-agents.sh

# Or manually start each agent
cd src/agents/document_agent && python __main__.py &
cd src/agents/credit_risk_agent && python __main__.py &
cd src/agents/compliance_agent && python __main__.py &
cd src/agents/routing_agent && python __main__.py &
"""
        )
        return False

    for name, card in available_agents.items():
        url = getattr(card, 'url', '')
        # Show agent name and URL on the same line
        if url:
            st.sidebar.markdown(f"<div style='display: flex; align-items: center; gap: 0.5rem;'><span style='font-weight:600; color:#155724;'>✅ {name}</span> <a href='{url}' style='font-size:0.95em;' target='_blank'>{url}</a></div>", unsafe_allow_html=True)
        else:
            st.sidebar.markdown(f"<span style='font-weight:600; color:#155724;'>✅ {name}</span>", unsafe_allow_html=True)
        st.sidebar.caption(f"📋 {getattr(card, 'description', '')}")

    return True


def display_processing_results(result: Dict[str, Any]):
    """Display the processing results in a structured format."""
    if "error" in result:
        st.markdown(f'<div class="error-box">❌ Error: {result["error"]}</div>', unsafe_allow_html=True)
        return

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["📊 Summary", "📄 Document Data", "⚖️ Risk Assessment", "🏛️ Compliance", "📋 Executive Summary"]
    )

    with tab1:
        display_summary_tab(result)

    with tab2:
        display_document_tab(result.get("document_data", {}))

    with tab3:
        display_risk_tab(result.get("risk_assessment", {}))

    with tab4:
        display_compliance_tab(result.get("compliance_result", {}))

    with tab5:
        display_executive_summary(result.get("summary", ""))

    display_pdf_download(result)


def display_summary_tab(result: Dict[str, Any]):
    col1, col2, col3 = st.columns(3)

    document_data = result.get("document_data", {}) or {}
    risk_assessment = result.get("risk_assessment", {}) or {}
    compliance_result = result.get("compliance_result", {}) or {}

    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Applicant", document_data.get("applicant_name", "Unknown"))
        income_val = document_data.get("income", None)
        income_display = f"${income_val:,}" if isinstance(income_val, (int, float)) else "N/A"
        st.metric("Annual Income", income_display)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        credit_score = risk_assessment.get("credit_score", "N/A")
        rating = None
        if isinstance(credit_score, (int, float)):
            if credit_score > 750:
                rating = "Excellent"
            elif credit_score > 700:
                rating = "Good"
            else:
                rating = "Fair"
        st.metric("Credit Score", credit_score, delta=rating)
        st.metric("Risk Level", str(risk_assessment.get("risk_level", "Unknown")).title())
        st.markdown("</div>", unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        approved = bool(compliance_result.get("approved", False))
        st.metric("Application Status", "APPROVED" if approved else "NOT APPROVED")
        conf = compliance_result.get("confidence", "N/A")
        conf_display = f"{conf:.1%}" if isinstance(conf, (int, float)) else str(conf)
        st.metric("Confidence", conf_display)
        st.markdown("</div>", unsafe_allow_html=True)


def display_document_tab(document_data: Dict[str, Any]):
    if not document_data:
        st.warning("No document data available")
        return

    st.markdown("### 📄 Extracted Document Information")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Personal Information**")
        info_data = {
            "Applicant Name": document_data.get("applicant_name", "N/A"),
            "Employment": document_data.get("employment", "N/A"),
            "Property Address": document_data.get("property_address", "N/A"),
        }
        for key, value in info_data.items():
            st.text(f"{key}: {value}")

    with col2:
        st.markdown("**Financial Information**")
        def money(v): return f"${v:,}" if isinstance(v, (int, float)) else "N/A"
        financial_data = {
            "Annual Income": money(document_data.get("income")),
            "Loan Amount": money(document_data.get("loan_amount")),
            "Property Value": money(document_data.get("property_value")),
            "Down Payment": money(document_data.get("down_payment")),
        }
        for key, value in financial_data.items():
            st.text(f"{key}: {value}")

    extracted = document_data.get("extracted_data", {}) or {}
    if extracted:
        st.markdown("**Additional Details**")
        additional_info = {
            "Monthly Income": money(extracted.get("monthly_income")),
            "Monthly Debt": money(extracted.get("monthly_debt")),
            "Assets": money(extracted.get("assets")),
            "Employment Years": f"{extracted.get('employment_years', 'N/A')} years",
        }
        for key, value in additional_info.items():
            st.text(f"{key}: {value}")


def display_risk_tab(risk_assessment: Dict[str, Any]):
    if not risk_assessment:
        st.warning("No risk assessment data available")
        return

    st.markdown("### ⚖️ Credit Risk Analysis")
    col1, col2, col3 = st.columns(3)

    with col1:
        level = str(risk_assessment.get("risk_level", "unknown")).lower()
        risk_color = "🟢" if level == "low" else "🟡" if level == "medium" else "🔴"
        st.markdown(f"**Risk Level:** {risk_color} {level.upper()}")

        score = risk_assessment.get("risk_score", 0)
        pct = (score / 100.0) if isinstance(score, (int, float)) and score >= 0 else 0.0
        pct = min(max(pct, 0.0), 1.0)
        st.progress(pct)
        st.caption(f"Risk Score: {score}/100")

    with col2:
        conf = risk_assessment.get("confidence", "N/A")
        st.markdown(f"**Confidence:** {conf:.1%}" if isinstance(conf, (int, float)) else f"**Confidence:** {conf}")

        credit_score = risk_assessment.get("credit_score", "N/A")
        st.markdown(f"**Credit Score:** {credit_score}")

    with col3:
        dti = risk_assessment.get("debt_to_income_ratio", "N/A")
        ltv = risk_assessment.get("loan_to_value_ratio", "N/A")
        st.markdown(f"**Debt-to-Income:** {dti:.1f}%" if isinstance(dti, (int, float)) else f"**Debt-to-Income:** {dti}")
        st.markdown(f"**Loan-to-Value:** {ltv:.1f}%" if isinstance(ltv, (int, float)) else f"**Loan-to-Value:** {ltv}")

    col1, col2 = st.columns(2)
    with col1:
        factors = risk_assessment.get("risk_factors", []) or []
        if factors:
            st.markdown("**⚠️ Risk Factors:**")
            for f in factors:
                st.markdown(f"• {f}")
        else:
            st.markdown("**✅ No significant risk factors identified**")
    with col2:
        recs = risk_assessment.get("recommendations", []) or []
        if recs:
            st.markdown("**💡 Recommendations:**")
            for r in recs:
                st.markdown(f"• {r}")


def display_compliance_tab(compliance_result: Dict[str, Any]):
    if not compliance_result:
        st.warning("No compliance data available")
        return

    st.markdown("### 🏛️ Regulatory Compliance")
    approved = bool(compliance_result.get("approved", False))
    decision_text = "APPROVED ✅" if approved else "NOT APPROVED ❌"
    (st.success if approved else st.error)(f"**Decision:** {decision_text}")

    conf = compliance_result.get("confidence", "N/A")
    st.info(f"**Confidence Level:** {conf:.1%}" if isinstance(conf, (int, float)) else f"**Confidence Level:** {conf}")

    col1, col2 = st.columns(2)
    with col1:
        issues = compliance_result.get("compliance_issues", []) or []
        if issues:
            st.markdown("**🚨 Compliance Issues:**")
            for issue in issues:
                st.error(f"• {issue}")
        else:
            st.success("**✅ No compliance issues identified**")
    with col2:
        recs = compliance_result.get("recommendations", []) or []
        if recs:
            st.markdown("**💡 Recommendations:**")
            for r in recs:
                st.info(f"• {r}")

    metrics = compliance_result.get("metrics", {}) or {}
    if metrics:
        st.markdown("**📊 Compliance Metrics:**")
        metrics_df = pd.DataFrame(list(metrics.items()), columns=["Metric", "Value"])
        st.dataframe(metrics_df, use_container_width=True)


def display_executive_summary(summary: str):
    if not summary:
        st.warning("No executive summary available")
        return
    st.markdown("### 📋 Executive Summary")
    st.markdown(summary)


def display_pdf_download(result: Dict[str, Any]):
    pdf_path = result.get("output_pdf_path")
    if not pdf_path:
        return
    path = Path(str(pdf_path))
    if path.exists():
        st.markdown("---")
        st.markdown("### 📥 Download Report")
        with open(path, "rb") as f:
            pdf_bytes = f.read()
        # Use a user-friendly download name while preserving the original file content.
        download_name = path.name if len(path.name) <= 80 else f"MortgageInsight_Report_{path.stat().st_mtime_ns}.pdf"
        st.download_button(
            label="📄 Download PDF Report",
            data=pdf_bytes,
            file_name=download_name,
            mime="application/pdf",
            type="primary",
        )
        st.success(f"✅ PDF report ready: {download_name}")


# ---- Main ---------------------------------------------------------------------------------------
def main():
    # --- Brand Bar: Logo left, title/subtitle right ---
    from PIL import Image
    st.markdown(
        """
<style>
.brand-bar{
  display:flex; align-items:center; justify-content:center; gap:1rem;
  padding:0.75rem 1rem; margin:0.25rem 0 1.2rem 0;
  background:#fff; border:1px solid #e9ecef; border-radius:14px;
  box-shadow:0 6px 24px rgba(31,78,121,.08);
}
.brand-title{font-size:2.25rem; font-weight:800; color:#1f4e79; margin:0;}
.brand-sub{margin:0.15rem 0 0 0; color:#55606f;}
@media (max-width: 640px){
  .brand-title{font-size:1.6rem;}
}
</style>
""",
        unsafe_allow_html=True,
    )

    logo_candidates = [
        project_root / "assets" / "logo.png",
        project_root / "fannie_mae_logo.png",
        Path("/mnt/data/376b68fd-5db3-4637-b637-efabd7651c47.png"),
    ]
    logo_img = None
    for p in logo_candidates:
        try:
            if p.exists():
                logo_img = Image.open(p)
                break
        except Exception:
            pass

    # Show logo at the very top of the sidebar, further reduced size
    if logo_img:
        st.sidebar.image(logo_img, width=90)

    # Main area: just title and subtitle, no shape
    st.markdown("<div class='brand-title' style='margin-bottom:0.2rem;'>MortgageInsight Pro</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='brand-sub'>AI-Powered Mortgage Analysis Platform — Upload your mortgage application PDF and get comprehensive analysis through our intelligent multi-agent system.</div>",
        unsafe_allow_html=True,
    )

    # Initialize app
    if "app" not in st.session_state:
        st.session_state.app = MortgageProcessorApp()
    app: MortgageProcessorApp = st.session_state.app

    # Discover agents (once)
    if not app.available_agents:
        with st.spinner("🔍 Discovering available agents..."):
            if not app.discover_agents_sync():
                st.stop()

    # Sidebar agent status
    if not display_agent_status(app.available_agents):
        st.stop()

    # Main layout
    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("### 📤 Upload Document")
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=["pdf"],
            help="Upload your mortgage application PDF document",
        )

        if uploaded_file is not None:
            st.success(f"✅ File uploaded: {uploaded_file.name}")
            st.markdown(f"**File size:** {uploaded_file.size:,} bytes")
            if st.button("🚀 Process Application", type="primary", use_container_width=True):
                with st.spinner("🔄 Processing mortgage application..."):
                    result = app.process_mortgage_application_sync(uploaded_file, uploaded_file.name)
                    st.session_state.processing_result = result
                    st.session_state.processing_complete = True
                    st.rerun()

    with col2:
        st.markdown("**📊 Processing Instructions**")
        st.markdown(
            """
1. **Upload PDF**: Select your mortgage application PDF file  
2. **Process**: Click the **Process Application** button  
3. **Review**: Examine the detailed analysis results  
4. **Download**: Get your comprehensive PDF report

**Supported Analysis:**
- 📄 Document data extraction
- ⚖️ Credit risk assessment
- 🏛️ Regulatory compliance check
- 📋 Executive summary generation
"""
        )

    if st.session_state.get("processing_complete", False) and "processing_result" in st.session_state:
        st.markdown("---")
        st.markdown("## 📊 Analysis Results")
        display_processing_results(st.session_state.processing_result)


if __name__ == "__main__":
    main()
