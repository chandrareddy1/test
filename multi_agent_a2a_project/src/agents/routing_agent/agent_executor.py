import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater

from src.agents.routing_agent.agent import RoutingAgent
from a2a.utils import (
    new_task,
    new_agent_text_message
)

from a2a.utils.errors import ServerError

from a2a.types import (
    Task,
    TaskState,
    UnsupportedOperationError
)

import asyncio
import json

class RoutingAgentExecutor(AgentExecutor):
    """
    Implements the AgentExecutor interface to integrate the 
    routing_agent with the A2A framework.
    """

    def __init__(self):
        self.agent = RoutingAgent()

    async def create(self):
        """
        Factory method to create and asynchronously initialize the RoutingAgentExecutor.
        """
        await self.agent.create()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        Executes the agent with the provided context and event queue.
        """
        query = context.get_user_input()
        task = context.current_task
        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)

        # Get context_id from different possible sources
        context_id = getattr(task, 'contextId', None) or getattr(context, 'context_id', None) or "default-context"
        
        updater = TaskUpdater(event_queue, task.id, context_id)
        
        try:
            # Start routing workflow
            await updater.update_status(
                TaskState.working,
                new_agent_text_message("Starting mortgage processing workflow...", context_id, task.id)
            )
            
            # Process query through routing workflow
            result = await self.agent.process_query(query)
            
            # Format the final result
            final_result = json.dumps(result, indent=2)
            
            await updater.update_status(
                TaskState.completed,
                new_agent_text_message(final_result, context_id, task.id)
            )

            await asyncio.sleep(0.1)  # Allow time for the message to be processed

        except Exception as e:
            error_message = f"Routing workflow error: {str(e)}"
            await updater.update_status(
                TaskState.failed,
                new_agent_text_message(error_message, context_id, task.id)
            )
            raise

    async def cancel(self, request: RequestContext, event_queue: EventQueue) -> Task | None:
        raise ServerError(error=UnsupportedOperationError())
