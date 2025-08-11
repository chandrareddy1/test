import asyncio
import uvicorn

from a2a.types import AgentSkill, AgentCard, AgentCapabilities
import asyncclick as click
from a2a.server.request_handlers import DefaultRequestHandler
from .agent import RoutingAgent
from .agent_executor import RoutingAgentExecutor
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.apps import A2AStarletteApplication

@click.command()
@click.option('--host', default='localhost', help='Host for the agent server')
@click.option('--port', default=10004, help='Port for the agent server')
async def main(host: str, port: int):
    """
    Main function to create and run the routing agent.
    """
    skill = AgentSkill(
        id="routing_agent_skill",
        name="routing_agent_skill",
        description="LangGraph-powered agent that orchestrates mortgage processing workflows using multiple specialized agents",
        tags=["routing", "orchestration", "workflow", "mortgage"],
        examples=[
            """process mortgage application end-to-end""",
            """route query to appropriate mortgage processing agents""",
            """orchestrate document extraction, risk assessment, and compliance checks"""
        ]
    )

    agent_card = AgentCard(
        name="routing_agent",
        description="A LangGraph-based orchestration agent that routes queries to appropriate mortgage processing agents",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=RoutingAgent.SUPPORTED_CONTENT_TYPES,    # Accepted input content types
        defaultOutputModes=RoutingAgent.SUPPORTED_CONTENT_TYPES,   # Supported features
        skills=[skill],
        capabilities=AgentCapabilities(streaming=True, pushNotifications=True),
    )

    # Create agent executor
    agent_executor = RoutingAgentExecutor()
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
