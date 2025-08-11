import asyncio
import uvicorn

from a2a.types import AgentSkill, AgentCard, AgentCapabilities
import asyncclick as click
from a2a.server.request_handlers import DefaultRequestHandler
from .agent import DocumentAgent
from .agent_executor import DocumentAgentExecutor
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.apps import A2AStarletteApplication

@click.command()
@click.option('--host', default='localhost', help='Host for the agent server')
@click.option('--port', default=10001, help='Port for the agent server')
async def main(host: str, port: int):
    """
    Main function to create and run the document agent.
    """
    skill = AgentSkill(
        id="document_agent_skill",
        name="document_agent_skill",
        description="AutoGen-powered agent that extracts details from a given input pdf document",
        tags=["document", "extraction", "pdf", "mortgage"],
        examples=[
            """extract the data from input pdf document""",
            """analyze mortgage application document""",
            """process loan application PDF"""
        ]
    )

    agent_card = AgentCard(
        name="document_agent",
        description="AutoGen-powered specialized agent for mortgage document analysis and data extraction",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=DocumentAgent.SUPPORTED_CONTENT_TYPES,    # Accepted input content types
        defaultOutputModes=DocumentAgent.SUPPORTED_CONTENT_TYPES,   # Supported features
        skills=[skill],
        capabilities=AgentCapabilities(streaming=True, pushNotifications=True),
    )

    # Create agent executor
    agent_executor = DocumentAgentExecutor()
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
