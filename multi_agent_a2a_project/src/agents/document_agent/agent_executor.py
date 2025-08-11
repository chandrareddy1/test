import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater

from src.agents.document_agent.agent import DocumentAgent
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

class DocumentAgentExecutor(AgentExecutor):
    """
    Implements the AgentExecutor interface to integrate the 
    document_agent with the A2A framework.
    """

    def __init__(self):
        self.agent = DocumentAgent()

    async def create(self):
        """
        Factory method to create and asynchronously initialize the DocumentAgentExecutor.
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
            async for item in self.agent.invoke(query, context_id):
                is_task_complete = item.get("is_task_complete", False)

                if not is_task_complete:
                    message = item.get('updates','The Agent is still working on your request.')
                    await updater.update_status(
                        TaskState.working,
                        new_agent_text_message(message, context_id, task.id)
                    )
                else:
                    final_result = item.get('content','no result received')
                    await updater.update_status(
                        TaskState.completed,
                        new_agent_text_message(final_result, context_id, task.id)
                    )

                    await asyncio.sleep(0.1)  # Allow time for the message to be processed

                    break
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            await updater.update_status(
                TaskState.failed,
                new_agent_text_message(error_message, context_id, task.id)
            )
            raise

    async def cancel(self, request: RequestContext, event_queue: EventQueue) -> Task | None:
        raise ServerError(error=UnsupportedOperationError())