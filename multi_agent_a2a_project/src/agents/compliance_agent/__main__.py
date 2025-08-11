import asyncio
import uvicorn

from a2a.types import AgentSkill, AgentCard, AgentCapabilities
import asyncclick as click
from a2a.server.request_handlers import DefaultRequestHandler
from .agent import ComplianceAgent
from .agent_executor import ComplianceAgentExecutor
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.apps import A2AStarletteApplication

@click.command()
@click.option('--host', default='localhost', help='Host for the agent server')
@click.option('--port', default=10003, help='Port for the agent server')
async def main(host: str, port: int):
    """
    Main function to create and run the compliance agent.
    """
    skill = AgentSkill(
        id="compliance_agent_skill",
        name="compliance_agent_skill",
        description="CrewAI-powered agent that performs compliance analysis for mortgage applications",
        tags=["compliance", "regulatory", "mortgage", "analysis"],
        examples=[
            """analyze mortgage application for compliance issues""",
            """check regulatory requirements and lending standards""",
            """evaluate Truth in Lending Act and Fair Housing Act compliance"""
        ]
    )

    agent_card = AgentCard(
        name="compliance_agent",
        description="CrewAI-powered specialized agent for mortgage compliance analysis and regulatory requirements",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=ComplianceAgent.SUPPORTED_CONTENT_TYPES,    # Accepted input content types
        defaultOutputModes=ComplianceAgent.SUPPORTED_CONTENT_TYPES,   # Supported features
        skills=[skill],
        capabilities=AgentCapabilities(streaming=True, pushNotifications=True),
    )

    # Create agent executor
    agent_executor = ComplianceAgentExecutor()
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
