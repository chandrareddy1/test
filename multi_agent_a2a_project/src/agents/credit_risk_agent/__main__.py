import asyncio
import uvicorn

from a2a.types import AgentSkill, AgentCard, AgentCapabilities
import asyncclick as click
from a2a.server.request_handlers import DefaultRequestHandler
from .agent import CreditRiskAgent
from .agent_executor import CreditRiskAgentExecutor
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.apps import A2AStarletteApplication

@click.command()
@click.option('--host', default='localhost', help='Host for the agent server')
@click.option('--port', default=10002, help='Port for the agent server')
async def main(host: str, port: int):
    """
    Main function to create and run the credit risk agent.
    """
    skill = AgentSkill(
        id="credit_risk_agent_skill",
        name="credit_risk_agent_skill",
        description="SmoAgents-powered agent that performs credit risk assessment for mortgage applications",
        tags=["credit", "risk", "assessment", "mortgage"],
        examples=[
            """assess credit risk for mortgage applicant""",
            """calculate debt-to-income ratio and risk factors""",
            """analyze financial stability and creditworthiness"""
        ]
    )

    agent_card = AgentCard(
        name="credit_risk_agent",
        description="SmoAgents-powered specialized agent for mortgage credit risk assessment and financial analysis",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=CreditRiskAgent.SUPPORTED_CONTENT_TYPES,    # Accepted input content types
        defaultOutputModes=CreditRiskAgent.SUPPORTED_CONTENT_TYPES,   # Supported features
        skills=[skill],
        capabilities=AgentCapabilities(streaming=True, pushNotifications=True),
    )

    # Create agent executor
    agent_executor = CreditRiskAgentExecutor()
    await agent_executor.create()

    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor,
        task_store=InMemoryTaskStore()
    )

    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler
    )

    # Fixed: Use uvicorn.Config and Server instead of uvicorn.run() to avoid
    # "asyncio.run() cannot be called from a running event loop" error
    config = uvicorn.Config(server.build(), host=host, port=port)
    server_instance = uvicorn.Server(config)
    
    await server_instance.serve()


if __name__ == "__main__":
    asyncio.run(main())